from models import DiagramElicitation, PhysicsAnswerElicitation
from mcp.server.fastmcp import Context, FastMCP
from typing import Any
import requests
import json


FASTAPI_BASE_URL = "http://127.0.0.1:8000"
DIAGRAM_API_BASE_URL = "http://127.0.0.1:7000"

mcp = FastMCP(
    "CBSE Physics RAG MCP Server",
    instructions=(
        "Expose the CBSE Physics RAG FastAPI services as MCP tools for "
        "retrieval, query classification, tool routing, and diagram generation."
    ),
    host="127.0.0.1",
    port=8100,
    stateless_http=False,
    json_response=False,
)

def _post_json(base_url: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{base_url}{path}", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def retrieve_physics_chunks(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Retrieve relevant physics textbook chunks for a student question."""
    data = _post_json(
        FASTAPI_BASE_URL,
        "/retrieve",
        {
            "query": query,
            "top_k": top_k,
        },
    )
    return data["results"]


@mcp.tool()
def classify_physics_query(question: str) -> str:
    """Classify a physics question as derivation, numerical, comparison, or theory."""
    data = _post_json(
        FASTAPI_BASE_URL,
        "/classify-query",
        {
            "question": question,
        },
    )
    return data["query_type"]


@mcp.tool()
def route_physics_tools(question: str) -> list[str]:
    """Decide which tools are needed for a physics question."""
    data = _post_json(
        FASTAPI_BASE_URL,
        "/route-tool",
        {
            "question": question,
        },
    )
    return data["tools"]


@mcp.tool()
def generate_physics_diagram(topic: str) -> dict[str, Any]:
    """Generate diagram metadata for a physics topic."""
    return _post_json(
        DIAGRAM_API_BASE_URL,
        "/generate-diagram",
        {
            "topic": topic,
        },
    )


@mcp.tool()
async def collect_physics_answer_preferences(
    ctx: Context,
    question: str = "",
) -> dict[str, Any]:
    """Ask the MCP client/user for missing answer details using elicitation."""
    result = await ctx.elicit(
        message=(
            "Please confirm the physics question and answer preferences. "
            "Use 'auto' for answer_mode if you want the tutor to classify it."
        ),
        schema=PhysicsAnswerElicitation,
    )

    if result.action != "accept":
        return {
            "status": result.action,
            "message": "The answer request was not confirmed.",
        }

    details = result.data.model_dump()
    if question and not details["question"]:
        details["question"] = question

    return {
        "status": "accepted",
        "details": details,
    }


@mcp.tool()
async def generate_physics_diagram_with_elicitation(
    ctx: Context,
    topic: str = "",
) -> dict[str, Any]:
    """Elicit missing diagram details, then call the diagram FastAPI service."""
    result = await ctx.elicit(
        message="Please confirm the physics diagram details.",
        schema=DiagramElicitation,
    )

    if result.action != "accept":
        return {
            "status": result.action,
            "message": "The diagram request was not confirmed.",
        }

    details = result.data.model_dump()
    diagram_topic = details["topic"] or topic
    if not diagram_topic:
        return {
            "status": "missing_topic",
            "message": "A diagram topic is required.",
        }

    diagram = generate_physics_diagram(diagram_topic)
    diagram["requested_diagram_type"] = details["diagram_type"]
    return diagram


@mcp.tool()
async def answer_physics_question_with_elicitation(
    ctx: Context,
    question: str = "",
) -> dict[str, Any]:
    """Elicit missing answer preferences, then run the full local RAG workflow."""
    result = await ctx.elicit(
        message=(
            "Please confirm the physics question before I run the textbook-grounded "
            "RAG workflow."
        ),
        schema=PhysicsAnswerElicitation,
    )

    if result.action != "accept":
        return {
            "status": result.action,
            "message": "The answer request was not confirmed.",
        }

    details = result.data.model_dump()
    final_question = details["question"] or question
    if not final_question:
        return {
            "status": "missing_question",
            "message": "A physics question is required.",
        }

    answer = answer_physics_question(final_question)
    answer["elicited_preferences"] = details
    return answer


@mcp.tool()
def answer_physics_question(question: str) -> dict[str, Any]:
    """Run the full local LangGraph RAG workflow for a physics question."""
    from workflow import app

    result = app.invoke({"question": question})
    return json.loads(json.dumps(result, default=str))


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
