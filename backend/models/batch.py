"""
Batch model for managing invoice batch processing
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class BatchStatus(str, enum.Enum):
    """Batch processing status"""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class Batch(Base):
    """Batch model"""
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Batch details
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(512))
    status = Column(Enum(BatchStatus), default=BatchStatus.CREATED, nullable=False, index=True)
    
    # Statistics
    total_invoices = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    pending_count = Column(Integer, default=0)
    flagged_count = Column(Integer, default=0)
    approved_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    
    # Progress
    progress_percentage = Column(Float, default=0.0)
    
    # Timing
    estimated_completion = Column(DateTime)
    processing_time = Column(Float, default=0.0)  # in seconds
    
    # User association
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    creator = relationship("User", back_populates="batches")
    invoices = relationship("Invoice", back_populates="batch", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="batch", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Batch {self.name} - {self.status.value}>"
    
    @property
    def batch_number(self) -> str:
        """Generate human-readable batch number"""
        return f"BATCH-{self.id:06d}"
    
    @property
    def is_active(self) -> bool:
        """Check if batch is actively processing"""
        return self.status in [BatchStatus.CREATED, BatchStatus.PROCESSING]
    
    @property
    def is_completed(self) -> bool:
        """Check if batch processing is completed"""
        return self.status == BatchStatus.COMPLETED
    
    def update_progress(self):
        """Update batch progress based on invoice counts"""
        if self.total_invoices > 0:
            self.progress_percentage = (self.processed_count / self.total_invoices) * 100
        else:
            self.progress_percentage = 0.0
        
        # Update status if all processed
        if self.total_invoices > 0 and self.processed_count == self.total_invoices:
            self.status = BatchStatus.COMPLETED
            self.completed_at = datetime.utcnow()
    
    def update_counts(self, db):
        """Update all counts from related invoices"""
        from models.invoice import Invoice, InvoiceStatus
        
        invoices = db.query(Invoice).filter(Invoice.batch_id == self.id).all()
        
        self.total_invoices = len(invoices)
        self.processed_count = sum(1 for inv in invoices if inv.is_completed)
        self.pending_count = sum(1 for inv in invoices if inv.status == InvoiceStatus.PENDING)
        self.flagged_count = sum(1 for inv in invoices if inv.is_flagged)
        self.approved_count = sum(1 for inv in invoices if inv.status == InvoiceStatus.APPROVED)
        self.rejected_count = sum(1 for inv in invoices if inv.status == InvoiceStatus.REJECTED)
        
        self.update_progress()
