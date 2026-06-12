---

# MCP Server

This project includes a real Model Context Protocol server in `mcp_server.py`.
It exposes the existing FastAPI services as MCP tools:

- `retrieve_physics_chunks`
- `classify_physics_query`
- `route_physics_tools`
- `generate_physics_diagram`
- `generate_physics_diagram_with_elicitation`
- `collect_physics_answer_preferences`
- `answer_physics_question`
- `answer_physics_question_with_elicitation`

Run the required FastAPI services in separate terminals:

```bash
uvicorn host_server:app --host 127.0.0.1 --port 9000
uvicorn local_mcp_server:app --host 127.0.0.1 --port 8000
uvicorn remote_mcp_server:app --host 127.0.0.1 --port 7000
```

Then start the MCP server:

```bash
python mcp_server.py
```

MCP clients can connect with Streamable HTTP at:

```text
http://127.0.0.1:8100/mcp
```

If you need to build or refresh the Chroma embeddings, run:

```bash
python semantic_search.py
```

The `*_with_elicitation` tools use MCP elicitation to ask the client/user for
missing details before running the tool. Your MCP client must support the
`elicitation` capability for these interactive tools. The MCP server is configured
with stateful Streamable HTTP/SSE because elicitation requires the server to send
requests back to the client during a tool call.

---

# Manim Video MCP Server

Physics concept videos are handled by a separate Manim service so video rendering
is only called when needed.

Run the Manim FastAPI backend:

```bash
uvicorn manim_video_server:app --host 127.0.0.1 --port 7100
```

Run the Manim MCP server:

```bash
python manim_mcp_server.py
```

MCP clients can connect to:

```text
http://127.0.0.1:8200/mcp
```

Tools:

- `should_generate_video`
- `generate_physics_video`
