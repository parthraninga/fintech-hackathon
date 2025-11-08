"""
Chat message model for conversational interface
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class MessageRole(str, enum.Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Association
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Subtasks (JSON array)
    subtasks = Column(JSON)  # [{"id": "1", "name": "...", "status": "..."}]
    
    # Metadata
    tokens_used = Column(Integer)
    model_used = Column(String(100))
    processing_time = Column(Float)  # in seconds
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    batch = relationship("Batch", back_populates="chat_messages")
    user = relationship("User", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage {self.role.value} - {self.timestamp}>"
    
    @property
    def is_user_message(self) -> bool:
        """Check if message is from user"""
        return self.role == MessageRole.USER
    
    @property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant"""
        return self.role == MessageRole.ASSISTANT
