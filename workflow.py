from Client_folder.manim_mcp_client import generate_physics_video_mcp
from Client_folder.mcp_client import (
    classify_query_mcp,
    generate_diagram_mcp,
    retrieve_chunks_mcp,
    route_tool_mcp,
)
from PDF_operations.chunks_logics import build_context
from langgraph.graph import END, StateGraph
from models import PhysicsRAGState
from openai import OpenAI
from prompt_templates import build_answer_prompt


client = OpenAI()


def build_prompt(mode, context, question):
    return build_answer_prompt(mode=mode, context=context, question=question)


def classify_question(state):
    query_type = classify_query_mcp(state.question)
    state.query_type = query_type
    state.execution_trace.append(f"classifier -> {query_type}")
    return state


def route_tool(state):
    tools = route_tool_mcp(state.question)
    state.selected_tools = tools
    state.execution_trace.append(f"tool_router -> {tools}")
    return state


def route_by_query_type(state):
    return state.query_type


def rewrite_query(state):
    state.rewritten_query = f"CBSE Physics {state.query_type} {state.question}"
    return state


def retrieval_node(state):
    chunks = retrieve_chunks_mcp(state.rewritten_query, top_k=5)
    if not chunks:
        state.no_context_found = True
        state.execution_trace.append("retrieval -> no chunks found")
        return state

    state.retrieved_chunks = chunks
    state.execution_trace.append(f"retrieval -> {len(chunks)} chunks")
    return state


def theory_generator(state):
    if state.no_context_found:
        state.final_prompt = None
        return state

    context = build_context(state.retrieved_chunks)
    state.final_prompt = build_prompt(mode="theory", context=context, question=state.question)
    state.execution_trace.append("generator -> theory prompt built")
    return state


def derivation_generator(state):
    if state.no_context_found:
        state.final_prompt = None
        return state

    context = build_context(state.retrieved_chunks)
    state.final_prompt = build_prompt(mode="derivation", context=context, question=state.question)
    state.execution_trace.append("generator -> derivation prompt built")
    return state


def numerical_generator(state):
    if state.no_context_found:
        state.final_prompt = None
        return state

    context = build_context(state.retrieved_chunks)
    state.final_prompt = build_prompt(mode="numerical", context=context, question=state.question)
    state.execution_trace.append("generator -> numerical prompt built")
    return state


def comparison_generator(state):
    if state.no_context_found:
        state.final_prompt = None
        return state

    context = build_context(state.retrieved_chunks)
    state.final_prompt = build_prompt(mode="comparison", context=context, question=state.question)
    state.execution_trace.append("generator -> comparison prompt built")
    return state


ANSWER_GENERATORS = {
    "theory": theory_generator,
    "derivation": derivation_generator,
    "numerical": numerical_generator,
    "comparison": comparison_generator,
}


def run_retrieval_tool(state):
    state.execution_trace.append("orchestrator -> retrieval pipeline")
    state = classify_question(state)
    state = rewrite_query(state)
    state = retrieval_node(state)

    if state.no_context_found:
        return state, None

    generator = ANSWER_GENERATORS.get(state.query_type)
    if generator is None:
        state.execution_trace.append(f"generator -> unsupported query type: {state.query_type}")
        return state, None

    state = generator(state)
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": state.final_prompt,
            }
        ],
    )
    return state, response.choices[0].message.content


def run_diagram_tool(state):
    state.execution_trace.append("orchestrator -> diagram tool")
    result = generate_diagram_mcp(state.question)
    image_path = result.get("image_path")
    if image_path:
        state.generated_diagrams.append(image_path)
        state.execution_trace.append("diagram_tool -> image generated")
        return state, "Diagram generated below."

    state.execution_trace.append("diagram_tool -> no image returned")
    return state, "Diagram generation failed: no image was returned."


def run_video_tool(state):
    state.execution_trace.append("orchestrator -> Manim video tool")
    result = generate_physics_video_mcp(
        topic=state.question,
        question=state.question,
        quality="low",
        render=True,
    )
    if not isinstance(result, dict):
        state.execution_trace.append("video_tool -> invalid result")
        return state, "Video generation failed: invalid result returned."

    if result.get("skipped"):
        state.execution_trace.append("video_tool -> skipped by LLM")
        return state, None

    rendered = bool(result.get("rendered"))
    video_path = result.get("video_path")
    if rendered and video_path:
        state.generated_videos.append(video_path)

    state.execution_trace.append("video_tool -> rendered" if rendered else "video_tool -> scene generated")
    status = "Rendered successfully." if rendered else "Scene code generated, but video rendering did not complete."
    return state, f"""
# Explanatory Video

Scene:
{result.get('scene_name')}

Scene file:
{result.get('scene_file')}

Rendered:
{result.get('rendered')}

Video path:
{result.get('video_path') or 'Not rendered'}

Status:
{status}
"""


TOOL_EXECUTORS = {
    "retrieval": run_retrieval_tool,
    "diagram_generation": run_diagram_tool,
    "video_generation": run_video_tool,
}


def orchestration_node(state):
    outputs = []
    for tool_name in state.selected_tools:
        executor = TOOL_EXECUTORS.get(tool_name)
        if executor is None:
            state.execution_trace.append(f"orchestrator -> unsupported tool: {tool_name}")
            continue

        state, output = executor(state)
        if output:
            outputs.append(output)

    state.final_answer = "\n\n".join(outputs)
    return state


def llm_node(state):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": state.final_prompt,
            }
        ],
    )
    state.final_answer = response.choices[0].message.content
    state.execution_trace.append("llm -> response generated")
    return state


graph = StateGraph(PhysicsRAGState)
# add nodes function here 
graph.add_node("route_tool", route_tool)
graph.add_node("orchestrator", orchestration_node)



#add graph edges here
graph.set_entry_point("route_tool")
graph.add_edge("route_tool", "orchestrator")
graph.add_edge("orchestrator", END)

app = graph.compile()


if __name__ == "__main__":
    png_data = app.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(png_data)
