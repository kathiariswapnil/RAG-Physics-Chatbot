from fastapi import FastAPI

try:
    from Server_files.models import DiagramRequest
    from Server_files.remote_mcp_server import create_diagram
except ModuleNotFoundError:
    from models import DiagramRequest
    from remote_mcp_server import create_diagram


app = FastAPI()


@app.post("/generate-fbd")
def generate_fbd(data: DiagramRequest):
    return create_diagram(data.topic)


@app.post("/generate-diagram")
def generate_diagram(data: DiagramRequest):
    return create_diagram(data.topic)


@app.get("/health")
def health():
    return {"status": "ok"}
