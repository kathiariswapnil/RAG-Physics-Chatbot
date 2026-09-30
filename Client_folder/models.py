from pydantic import BaseModel, Field

class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    book: str
    page_number: int
    chunk_number: int