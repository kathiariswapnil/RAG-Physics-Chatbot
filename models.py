from pydantic import BaseModel, Field
from typing import List, Optional
from Client_folder.models import RetrievedChunk


class PhysicsChunk(BaseModel):
    chunk_id: str
    book: str
    page_number: int
    chunk_number: int
    content: str
    images: List[str] = []
    topic: Optional[str] = None
    chunk_type: Optional[str] = None
    
class EmbeddedChunk(PhysicsChunk):
    embedding: List[float]

class PDFPage(BaseModel):
    book: str
    page_number: int
    text: str
    images: List[str]
    
class RetrievalResult(BaseModel):
    chunk_id: str
    content: str
    similarity_score: float
    metadata: dict
    
class BoardAnswer(BaseModel):
    question: str
    introduction: str
    theory: List[str]
    derivation: List[str]
    formulas: List[str]
    conclusion: str
    references: List[str]
    
class PhysicsRAGState(BaseModel):
    question: str
    execution_trace: list[str] = Field(default_factory=list)
    query_type: str = ""
    rewritten_query: str = ""
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    no_context_found: bool = False
    final_prompt: str = ""
    draft_answer: str = ""
    selected_tools: list[str] = Field(default_factory=list)
    generated_diagrams: list[str] = Field(default_factory=list)
    generated_videos: list[str] = Field(default_factory=list)
    final_answer: str = ""
