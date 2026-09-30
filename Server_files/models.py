from pydantic import BaseModel, Field
from typing import List, Optional

class SampleRequest(BaseModel):
    prompt: str
    
class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5
    
class ClassificationRequest(BaseModel):
    question: str
    
class ToolRoutingRequest(BaseModel):
    question: str
    
class VideoRequest(BaseModel):
    topic: str
    question: str = ""
    quality: str = "low"
    render: bool = True
    
class DiagramRequest(BaseModel):
    topic: str
    
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
    
class PhysicsAnswerElicitation(BaseModel):
    question: str = Field(
        default="",
        description="The full physics question to answer.",
    )
    answer_mode: str = Field(
        default="auto",
        description="Answer style: auto, theory, derivation, numerical, or comparison.",
    )
    include_diagram: bool = Field(
        default=False,
        description="Whether the answer should include a physics diagram when useful.",
    )
    top_k: int = Field(
        default=5,
        description="Number of textbook chunks to retrieve.",
    )

class DiagramElicitation(BaseModel):
    topic: str = Field(
        default="",
        description="The physics topic or situation to diagram.",
    )
    diagram_type: str = Field(
        default="auto",
        description="Diagram type, for example free_body_diagram, graph, circuit, or auto.",
    )