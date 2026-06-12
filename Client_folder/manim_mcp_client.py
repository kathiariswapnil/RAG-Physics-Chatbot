from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
from typing import Any
import asyncio
import json


MANIM_MCP_URL = "http://127.0.0.1:8200/mcp"


async def _call_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
    async with streamable_http_client(MANIM_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            if result.structuredContent is not None:
                return result.structuredContent
            if result.content:
                text = result.content[0].text
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
            return None


async def should_generate_video_async(question: str) -> bool:
    result = await _call_tool("should_generate_video", {"question": question})
    if isinstance(result, dict) and "generate_video" in result:
        return bool(result["generate_video"])
    if isinstance(result, dict) and "result" in result:
        nested = result["result"]
        if isinstance(nested, dict) and "generate_video" in nested:
            return bool(nested["generate_video"])
        return bool(nested)
    return bool(result)


async def generate_physics_video_async(
    topic: str,
    question: str = "",
    quality: str = "low",
    render: bool = True,
) -> Any:
    return await _call_tool(
        "generate_physics_video",
        {
            "topic": topic,
            "question": question,
            "quality": quality,
            "render": render,
        },
    )


def should_generate_video_mcp(question: str) -> bool:
    return asyncio.run(should_generate_video_async(question))


def generate_physics_video_mcp(
    topic: str,
    question: str = "",
    quality: str = "low",
    render: bool = True,
) -> Any:
    return asyncio.run(generate_physics_video_async(topic, question, quality, render))


if __name__ == "__main__":
    sample_question = "Create an animation explaining projectile motion"
    print(should_generate_video_mcp(sample_question))
    print(generate_physics_video_mcp("projectile motion", sample_question, render=False))
