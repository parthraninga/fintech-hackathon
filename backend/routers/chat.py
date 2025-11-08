"""
Chat router for conversational interface
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models.user import User
from models.batch import Batch
from models.chat import ChatMessage, MessageRole
from schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatMessage as ChatMessageSchema
from dependencies import get_current_user

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response
    """
    # Verify batch exists
    batch = db.query(Batch).filter(Batch.id == request.batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Check access
    from models.user import UserRole
    if current_user.role != UserRole.ADMIN and batch.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this batch"
        )
    
    # Save user message
    user_message = ChatMessage(
        batch_id=request.batch_id,
        user_id=current_user.id,
        role=MessageRole.USER,
        content=request.message
    )
    db.add(user_message)
    db.commit()
    
    # Generate AI response (mock for now)
    # In production, integrate with OpenAI or your AI model
    ai_response_content = f"Processing your request: {request.message}"
    
    # Mock subtasks
    subtasks = [
        {"id": "1", "name": "Analyzing batch data", "status": "completed", "progress": 100},
        {"id": "2", "name": "Generating insights", "status": "in-progress", "progress": 60}
    ]
    
    # Save AI response
    ai_message = ChatMessage(
        batch_id=request.batch_id,
        user_id=current_user.id,
        role=MessageRole.ASSISTANT,
        content=ai_response_content,
        subtasks=subtasks
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    return ChatResponse(
        message=ChatMessageSchema(
            role=ai_message.role,
            content=ai_message.content,
            subtasks=ai_message.subtasks,
            timestamp=ai_message.timestamp
        ),
        processing_time=0.5
    )


@router.get("/history/{batch_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat history for a batch
    """
    # Verify batch exists and user has access
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    from models.user import UserRole
    if current_user.role != UserRole.ADMIN and batch.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this batch"
        )
    
    # Get chat messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.batch_id == batch_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    return ChatHistoryResponse(
        batch_id=batch_id,
        messages=[
            ChatMessageSchema(
                role=msg.role,
                content=msg.content,
                subtasks=msg.subtasks,
                timestamp=msg.timestamp
            )
            for msg in messages
        ],
        total=len(messages)
    )
