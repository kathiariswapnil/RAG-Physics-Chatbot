# CBSE Physics RAG Tutor

An MCP-powered Physics RAG chatbot that delivers textbook-grounded answers with intelligent LLM tool routing for diagrams, Manim animations, and interactive learning workflows.

The system answers CBSE-style physics questions using Retrieval-Augmented Generation over textbook content, then routes requests to specialized tools when the user needs diagrams or explanatory animations.

## Features

- Textbook-grounded RAG over HC Verma and IE Irodov content.
- CBSE-style theory, derivation, numerical, and comparison answers.
- LLM-based tool routing for retrieval, diagram generation, and video generation.
- MCP servers and clients for modular tool execution.
- Generated physics diagrams rendered as images in Streamlit.
- Manim-based explanatory animations rendered as MP4 videos.
- Prompt templates for classification, routing, answer generation, and video-decision prompts.
- Persistent Streamlit chat history backed by database operations.

## Architecture

```text
Streamlit UI
    |
LangGraph workflow
    |
LLM router
    |
    +-- Retrieval MCP/FastAPI service -> ChromaDB textbook chunks
    +-- Diagram service -> generated PNG diagrams
    +-- Manim service -> generated scene code and MP4 videos
```

The workflow does not call every tool for every query. The LLM router selects the required tools, and the dispatcher executes only those selected tools.

## Project Structure

```text
Client_folder/          MCP client wrappers
Server_files/           FastAPI and MCP servers
PDF_operations/         PDF extraction and chunking utilities
Database_operations/    Conversation persistence
prompt_templates.py     Reusable prompt templates
workflow.py             LangGraph orchestration
st_app.py               Streamlit chat UI
models.py               Shared workflow state models
```

## Core Services

### Host LLM Service

Provides a local FastAPI wrapper around the OpenAI chat model.

```bash
uvicorn Server_files.host_server:app --host 127.0.0.1 --port 9000
```

### Local Retrieval and Routing Service

Handles semantic retrieval, query classification, and LLM tool routing.

```bash
uvicorn Server_files.local_mcp_server:app --host 127.0.0.1 --port 8000
```

### Diagram Service

Generates actual PNG diagrams instead of returning metadata-only responses.

```bash
uvicorn Server_files.remote_mcp_server:app --host 127.0.0.1 --port 7000
```

### Main MCP Server

Exposes the core Physics RAG tools over MCP.

```bash
python Server_files\mcp_server.py
```

Default endpoint:

```text
http://127.0.0.1:8100/mcp
```

### Manim Video Backend

Generates Manim scene code and renders MP4 videos when selected by the LLM router.

```bash
uvicorn Server_files.manim_video_server:app --host 127.0.0.1 --port 7100
```

### Manim MCP Server

Exposes Manim video generation through MCP.

```bash
python Server_files\manim_mcp_server.py
```

Default endpoint:

```text
http://127.0.0.1:8200/mcp
```

### Streamlit App

```bash
streamlit run st_app.py
```

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your OpenAI API key before running the services:

```bash
set OPENAI_API_KEY=your_api_key_here
```

For Manim video rendering, make sure Manim and FFmpeg are available. If rendering is unavailable, the service can still generate Manim scene files.

## Embeddings

The vector database uses ChromaDB. To build or refresh embeddings from processed chunks:

```bash
python Server_files\semantic_search.py
```

The expected chunk file is:

```text
processed_data/chunks/all_chunks.json
```

## Prompt Templates

Reusable prompts are centralized in:

```text
prompt_templates.py
```

Current templates include:

- answer generation
- query classification
- tool routing
- video-generation decision

## Generated Outputs

Generated artifacts are ignored by Git:

```text
generated_diagrams/
generated_manim/
physics_chroma_db/
processed_data/
Books/
```

These folders may be large and should be regenerated locally.

## Example Queries

```text
Derive the expression for escape velocity.
```

```text
Explain projectile motion and draw its trajectory graph.
```

```text
Create an animation explaining momentum.
```

## Notes

- Ordinary theory, derivation, numerical, and comparison queries do not trigger Manim.
- Static diagram requests call the diagram service, not the video service.
- Animation/video requests are decided by the LLM router and the Manim MCP server's LLM decision prompt.
- Answers are instructed to stay grounded in retrieved textbook context.
