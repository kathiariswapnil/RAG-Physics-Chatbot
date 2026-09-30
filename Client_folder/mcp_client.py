from Client_folder.models import RetrievedChunk
import requests


BASE_URL = "http://127.0.0.1:8000"
REMOTE_MCP_URL = "http://127.0.0.1:7000"


def retrieve_chunks_mcp(query, top_k=5):
    try:
        response = requests.post(
            f"{BASE_URL}/retrieve",
            json={
                "query": query,
                "top_k": top_k
            }
        )
        response.raise_for_status()
        data = response.json()
        return [RetrievedChunk(**chunk) for chunk in data["results"]]
    except Exception as e:
        print(f"MCP Retrieval Error: {e}")
        return []


def classify_query_mcp(question):
    response = requests.post(
        f"{BASE_URL}/classify-query",
        json={
            "question": question
        }
    )
    response.raise_for_status()
    return response.json()["query_type"]

def generate_diagram_mcp(topic):
    response = requests.post(
        f"{REMOTE_MCP_URL}/generate-diagram",
        json={
            "topic": topic
        }
    )
    response.raise_for_status()
    return response.json()


def route_tool_mcp(question):
    response = requests.post(
        f"{BASE_URL}/route-tool",
        json={
            "question": question
        }
    )
    response.raise_for_status()
    return response.json()["tools"]