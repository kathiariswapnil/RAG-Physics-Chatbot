from models import PhysicsChunk
from pathlib import Path
import json
import os
import re


INPUT_FOLDER = "processed_data/pages"
OUTPUT_FOLDER = "processed_data/chunks"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\bPage\s+\d+\b", "", text)
    text = text.replace("\x0c", "")
    return text.strip()

def split_into_paragraphs(text):
    paragraphs = re.split(r'(?<=[.!?])\s+', text)
    return paragraphs

def create_chunks(text, chunk_size=1200, overlap=200):
    paragraphs = split_into_paragraphs(text)
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) > chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = current_chunk[-overlap:] + " " + para
        else:
            current_chunk += " " + para
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks

def process_page_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        page_data = json.load(f)
    cleaned_text = clean_text(page_data["text"])
    chunk_texts = create_chunks(cleaned_text)
    structured_chunks = []
    for idx, chunk_text in enumerate(chunk_texts):
        chunk = PhysicsChunk(
            chunk_id=(
                f"{page_data['book']}"
                f"_p{page_data['page_number']}"
                f"_c{idx}"
            ),
            book=page_data["book"],
            page_number=page_data["page_number"],
            chunk_number=idx,
            content=chunk_text,
            images=page_data.get("images", [])
        )
        structured_chunks.append(chunk)
    return structured_chunks

def build_context(chunks):
    context = ""
    for chunk in chunks:
        context += f"""

SOURCE:
Book: {chunk.book}

Page: {chunk.page_number}

CONTENT:
{chunk.content}

====================
"""
    return context

if __name__ == "__main__":
    all_chunks = []
    json_files = Path(INPUT_FOLDER).glob("*.json")
    for json_file in json_files:
        print(f"Processing: {json_file.name}")
        chunks = process_page_json(json_file)
        all_chunks.extend(chunks)
    # convert Pydantic objects
    serializable_chunks = [chunk.model_dump()for chunk in all_chunks]
    output_path = os.path.join(OUTPUT_FOLDER,"all_chunks.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            serializable_chunks,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"\nTotal Chunks: "
        f"{len(all_chunks)}"
    )
    print(
        f"Saved to: "
        f"{output_path}"
    )