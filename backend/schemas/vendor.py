"""
Vendor schemas for vendor management
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VendorBase(BaseModel):
    """Base vendor schema"""
    gstin: str = Field(..., min_length=15, max_length=15)
    name: str


class VendorCreate(VendorBase):
    """Schema for vendor creation"""
    legal_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class VendorUpdate(BaseModel):
    """Schema for vendor update"""
    name: Optional[str] = None
    legal_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_blacklisted: Optional[bool] = None
    blacklist_reason: Optional[str] = None


class VendorStats(BaseModel):
    """Schema for vendor statistics"""
    total_invoices: int
    flagged_count: int
    approved_count: int
    rejected_count: int
    total_amount: float
    flagged_percentage: float
    approval_rate: float


class VendorResponse(VendorBase):
    """Schema for vendor response"""
    id: int
    risk_score: float
    risk_category: Optional[str] = None
    is_blacklisted: bool
    total_invoices: int
    flagged_count: int
    created_at: datetime
    last_invoice_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VendorDetailResponse(VendorResponse):
    """Schema for detailed vendor response"""
    legal_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    blacklist_reason: Optional[str] = None
    approved_count: int
    rejected_count: int
    total_amount: float
    
    class Config:
        from_attributes = True
