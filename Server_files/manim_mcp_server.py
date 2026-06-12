from typing import Any
import requests
import json
from mcp.server.fastmcp import FastMCP

try:
    from prompt_templates import build_video_generation_decision_prompt
except ModuleNotFoundError:
    from pathlib import Path
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from prompt_templates import build_video_generation_decision_prompt


MANIM_API_BASE_URL = "http://127.0.0.1:7100"
LLM_API_URL = "http://127.0.0.1:9000/sample"

mcp = FastMCP(
    "Physics Manim Video MCP Server",
    instructions=(
        "Generate explanatory Manim videos for physics concepts. Use this server "
        "only when the user explicitly asks for a video, animation, animated "
        "explanation, motion visualization, or step-by-step visual walkthrough."
    ),
    host="127.0.0.1",
    port=8200,
    stateless_http=True,
    json_response=True,
)


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def decide_video_generation(question: str) -> dict[str, Any]:
    """Use the LLM router to decide whether a Manim animation is required."""
    try:
        response = requests.post(
            LLM_API_URL,
            json={"prompt": build_video_generation_decision_prompt(question)},
            timeout=120,
        )
        response.raise_for_status()
        raw_output = response.json()["output"]
        decision = _extract_json_object(raw_output)
    except Exception as exc:
        return {
            "generate_video": False,
            "reason": f"LLM video decision failed: {exc}",
        }

    return {
        "generate_video": bool(decision.get("generate_video")),
        "reason": str(decision.get("reason", "")).strip() or "No reason provided.",
    }


def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{MANIM_API_BASE_URL}{path}", json=payload, timeout=240)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def should_generate_video(question: str) -> dict[str, Any]:
    """Use the LLM to decide whether the Manim video tool is required."""
    return decide_video_generation(question)


@mcp.tool()
def generate_physics_video(
    topic: str,
    question: str = "",
    quality: str = "low",
    render: bool = True,
) -> dict[str, Any]:
    """Generate Manim scene code and render an explanatory physics video when available."""
    decision = decide_video_generation(question or topic)
    if not decision["generate_video"]:
        return {
            "skipped": True,
            "reason": decision["reason"],
            "topic": topic,
            "decision_source": "llm",
        }

    result = _post_json(
        "/generate-video",
        {
            "topic": topic,
            "question": question,
            "quality": quality,
            "render": render,
        },
    )
    result["skipped"] = False
    result["decision_reason"] = decision["reason"]
    result["decision_source"] = "llm"
    return result


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
