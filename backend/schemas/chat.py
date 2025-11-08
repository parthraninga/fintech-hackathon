"""
Chat schemas for conversational interface
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from models.chat import MessageRole


class Subtask(BaseModel):
    """Schema for chat subtask"""
    id: str
    name: str
    status: str  # "pending", "in-progress", "completed", "failed"
    progress: Optional[int] = Field(None, ge=0, le=100)


class ChatMessage(BaseModel):
    """Schema for chat message"""
    role: MessageRole
    content: str
    subtasks: Optional[List[Subtask]] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat request"""
    batch_id: int
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    """Schema for chat response"""
    message: ChatMessage
    processing_time: Optional[float] = None


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response"""
    batch_id: int
    messages: List[ChatMessage]
    total: int


class StreamChunk(BaseModel):
    """Schema for streaming chat chunk"""
    type: str  # "content", "subtask", "complete"
    content: Optional[str] = None
    subtask: Optional[Subtask] = None
    done: bool = False
