from fastapi import FastAPI
import requests
import json

try:
    from Server_files.semantic_search import retrieve_chunks
except ModuleNotFoundError:
    from semantic_search import retrieve_chunks

try:
    from Server_files.models import RetrievalRequest, ClassificationRequest, ToolRoutingRequest
except ModuleNotFoundError:
    from models import RetrievalRequest, ClassificationRequest, ToolRoutingRequest

try:
    from prompt_templates import build_classification_prompt, build_tool_routing_prompt
except ModuleNotFoundError:
    from pathlib import Path
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from prompt_templates import build_classification_prompt, build_tool_routing_prompt

app = FastAPI()
ALLOWED_TOOLS = {"retrieval", "diagram_generation", "video_generation"}


def parse_tool_list(output: str) -> list[str]:
    try:
        raw_tools = json.loads(output)
    except json.JSONDecodeError:
        return ["retrieval"]

    if not isinstance(raw_tools, list):
        return ["retrieval"]

    tools = [
        tool
        for tool in raw_tools
        if tool in ALLOWED_TOOLS
    ]
    return tools or ["retrieval"]


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/retrieve")
def retrieve(data: RetrievalRequest):
    results = retrieve_chunks(data.query, top_k = data.top_k)
    return {"results": results}
    
@app.post("/classify-query")
def classify_query(data: ClassificationRequest):
    prompt = build_classification_prompt(data.question)
    response = requests.post(
        "http://127.0.0.1:9000/sample",
        json={
            "prompt": prompt
        }
    )
    response.raise_for_status()
    output = response.json()["output"].strip().lower()
    return {"query_type": output}

# @app.post("/get-citations")


# @app.post("/generate-diagram")

@app.post("/route-tool")
def route_tool(data: ToolRoutingRequest):

    prompt = build_tool_routing_prompt(data.question)

    response = requests.post(
        "http://127.0.0.1:9000/sample",
        json={
            "prompt": prompt
        }
    )

    response.raise_for_status()

    output = response.json()["output"].strip()

    tools = parse_tool_list(output)

    return {
        "tools": tools
    }
