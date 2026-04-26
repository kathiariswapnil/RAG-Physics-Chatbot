from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone


Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    conversation = relationship("Conversation", back_populates="messages")

class PDFPage(BaseModel):
    book: str
    page_number: int
    text: str
    images: List[str]
    
class PhysicsChunk(BaseModel):
    chunk_id: str
    book: str
    page_number: int
    chunk_number: int
    content: str
    images: List[str] = []
    topic: Optional[str] = None
    chunk_type: Optional[str] = None
    
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
    
class PhysicsChunk(BaseModel):
    chunk_id: str
    book: str
    page_number: int
    chunk_number: int
    content: str
    images: List[str] = []

class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    book: str
    page_number: int
    chunk_number: int

class EmbeddedChunk(PhysicsChunk):
    embedding: List[float]
    
class PhysicsRAGState(BaseModel):
    question: str
    query_type: str = ""
    rewritten_query: str = ""
    retrieved_chunks: List[RetrievedChunk] = []
    no_context_found: bool = False
    final_prompt: str = ""
    draft_answer: str = ""
    final_answer: str = ""