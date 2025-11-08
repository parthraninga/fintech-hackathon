"""
Batch schemas for batch management
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.batch import BatchStatus


class BatchBase(BaseModel):
    """Base batch schema"""
    name: str
    description: Optional[str] = None


class BatchCreate(BatchBase):
    """Schema for batch creation"""
    pass


class BatchUpdate(BaseModel):
    """Schema for batch update"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BatchStatus] = None


class BatchStats(BaseModel):
    """Schema for batch statistics"""
    total_invoices: int
    processed_count: int
    pending_count: int
    flagged_count: int
    approved_count: int
    rejected_count: int
    progress_percentage: float


class BatchResponse(BatchBase):
    """Schema for batch response"""
    id: int
    status: BatchStatus
    total_invoices: int
    processed_count: int
    progress_percentage: float
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BatchDetailResponse(BatchResponse):
    """Schema for detailed batch response"""
    pending_count: int
    flagged_count: int
    approved_count: int
    rejected_count: int
    processing_time: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BatchListResponse(BaseModel):
    """Schema for paginated batch list"""
    items: list[BatchResponse]
    total: int
    page: int
    page_size: int
    pages: int
