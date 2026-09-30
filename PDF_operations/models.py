from pydantic import BaseModel, Field
from typing import List, Optional


class PhysicsChunk(BaseModel):
    chunk_id: str
    book: str
    page_number: int
    chunk_number: int
    content: str
    images: List[str] = []
    topic: Optional[str] = None
    chunk_type: Optional[str] = None