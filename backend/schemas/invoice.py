"""
Invoice schemas for invoice processing and management
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from models.invoice import InvoiceStatus, AgentStage


class ExtractedData(BaseModel):
    """Schema for extracted invoice data"""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    vendor_gstin: Optional[str] = None
    vendor_name: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    taxable_amount: Optional[float] = None
    currency: Optional[str] = "INR"
    line_items: Optional[List[Dict[str, Any]]] = None
    raw_data: Optional[Dict[str, Any]] = None


class InvoiceBase(BaseModel):
    """Base invoice schema"""
    filename: str
    batch_id: int


class InvoiceCreate(InvoiceBase):
    """Schema for invoice creation"""
    file_path: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None


class InvoiceUpdate(BaseModel):
    """Schema for invoice update"""
    status: Optional[InvoiceStatus] = None
    current_stage: Optional[AgentStage] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    extracted_data: Optional[Dict[str, Any]] = None
    is_flagged: Optional[bool] = None
    flag_reasons: Optional[List[str]] = None


class InvoiceStatusUpdate(BaseModel):
    """Schema for invoice status update (approve/reject)"""
    status: InvoiceStatus
    reason: Optional[str] = None


class InvoiceFilter(BaseModel):
    """Schema for invoice filtering"""
    batch_id: Optional[int] = None
    vendor_id: Optional[int] = None
    status: Optional[InvoiceStatus] = None
    is_flagged: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None  # Search in invoice_number, vendor_name
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class InvoiceResponse(BaseModel):
    """Schema for invoice response"""
    id: int
    batch_id: int
    vendor_id: Optional[int] = None
    filename: str
    file_path: str
    status: InvoiceStatus
    current_stage: AgentStage
    progress_percentage: float
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    vendor_gstin: Optional[str] = None
    vendor_name: Optional[str] = None
    total_amount: Optional[float] = None
    is_flagged: bool
    flag_reasons: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InvoiceDetailResponse(InvoiceResponse):
    """Schema for detailed invoice response with full data"""
    extracted_data: Optional[Dict[str, Any]] = None
    ocr_text: Optional[str] = None
    validation_errors: Optional[List[str]] = None
    processing_time: Optional[float] = None
    
    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list"""
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    pages: int
