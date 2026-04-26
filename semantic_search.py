from openai import OpenAI
from models import PhysicsChunk, EmbeddedChunk
import chromadb
import json

COLLECTION_NAME = "physics_chunks"

client = OpenAI()


chroma_client = chromadb.PersistentClient(path="physics_chroma_db")
collection = chroma_client.get_or_create_collection(name="physics_chunks")

def generate_embedding(text):
    response = client.embeddings.create(model="text-embedding-3-large", input=text)
    return response.data[0].embedding

def retrieve_chunks(query,top_k=5):
    query_embedding = generate_embedding(query)
    results = collection.query(query_embeddings=[query_embedding],n_results=top_k)
    retrieved = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    ids = results["ids"][0]
    for doc, meta, chunk_id in zip(documents, metadatas, ids):
        retrieved.append({
            "chunk_id":
                chunk_id,
            "content":
                doc,
            "book":
                meta["book"],
            "page_number":
                meta["page_number"],
            "chunk_number":
                meta["chunk_number"]
        })

    return retrieved

existing_collections = [c.name for c in chroma_client.list_collections()]

if COLLECTION_NAME in existing_collections:
    print("Loading existing collection...")
    collection = chroma_client.get_collection(COLLECTION_NAME)
else:
    print("Creating new collection...")
    collection = chroma_client.create_collection(name=COLLECTION_NAME)

with open(
    "processed_data/chunks/all_chunks.json",
    "r",
    encoding="utf-8"
) as f:
    raw_chunks = json.load(f)
chunks = [PhysicsChunk(**chunk) for chunk in raw_chunks]

for chunk in chunks:
    existing = collection.get(ids=[chunk.chunk_id])
    if existing["ids"]:
        print(f"Skipping existing: "f"{chunk.chunk_id}")
        continue
    
    print(f"Embedding: {chunk.chunk_id}")
    embedding = generate_embedding(chunk.content)
    embedded_chunk = EmbeddedChunk(**chunk.model_dump(), embedding=embedding)
    collection.add(
        ids=[embedded_chunk.chunk_id],
        embeddings=[embedded_chunk.embedding],
        documents=[embedded_chunk.content],
        metadatas=[{
            "book": embedded_chunk.book,
            "page_number": embedded_chunk.page_number,
            "chunk_number": embedded_chunk.chunk_number
        }]
    )

print("\nEmbedding storage complete.")