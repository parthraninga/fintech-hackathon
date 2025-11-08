"""
Invoice model for storing invoice processing data
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, JSON, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"


class AgentStage(str, enum.Enum):
    """Agent processing stages"""
    UPLOAD = "upload"
    OCR = "ocr"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    ARITHMETIC = "arithmetic"
    DUPLICATION = "duplication"
    FLAGGING = "flagging"
    REVIEW = "review"


class Invoice(Base):
    """Invoice model"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    
    # Processing status
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING, nullable=False, index=True)
    current_stage = Column(Enum(AgentStage), default=AgentStage.UPLOAD, nullable=False)
    progress_percentage = Column(Float, default=0.0)
    
    # Extracted data (JSON)
    extracted_data = Column(JSON)
    ocr_text = Column(Text)
    
    # Invoice details
    invoice_number = Column(String(100), index=True)
    invoice_date = Column(DateTime)
    due_date = Column(DateTime)
    vendor_gstin = Column(String(15), index=True)
    vendor_name = Column(String(255))
    total_amount = Column(Float)
    tax_amount = Column(Float)
    taxable_amount = Column(Float)
    currency = Column(String(10), default="INR")
    
    # Validation & Flags
    is_flagged = Column(Boolean, default=False, index=True)
    flag_reasons = Column(JSON)  # Array of flag reasons
    confidence_score = Column(Float)
    validation_errors = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    approved_at = Column(DateTime)
    rejected_at = Column(DateTime)
    
    # Relationships
    batch = relationship("Batch", back_populates="invoices")
    vendor = relationship("Vendor", back_populates="invoices")
    
    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.status.value}>"
    
    @property
    def is_completed(self) -> bool:
        """Check if invoice processing is completed"""
        return self.status in [InvoiceStatus.COMPLETED, InvoiceStatus.APPROVED, InvoiceStatus.REJECTED]
    
    @property
    def processing_time(self) -> float:
        """Get processing time in seconds"""
        if self.processed_at and self.created_at:
            return (self.processed_at - self.created_at).total_seconds()
        return 0.0
