"""
Vendor model for vendor management and risk scoring
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Vendor(Base):
    """Vendor model"""
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Vendor details
    gstin = Column(String(15), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(255))
    address = Column(String(512))
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    country = Column(String(100), default="India")
    
    # Contact information
    email = Column(String(255))
    phone = Column(String(20))
    contact_person = Column(String(255))
    
    # Risk & Analytics
    risk_score = Column(Float, default=0.0, index=True)  # 0-100
    risk_category = Column(String(20))  # "low", "medium", "high"
    is_blacklisted = Column(Boolean, default=False, index=True)
    blacklist_reason = Column(String(512))
    
    # Statistics
    total_invoices = Column(Integer, default=0)
    flagged_count = Column(Integer, default=0)
    approved_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_invoice_date = Column(DateTime)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="vendor")
    
    def __repr__(self):
        return f"<Vendor {self.gstin} - {self.name}>"
    
    @property
    def flagged_percentage(self) -> float:
        """Calculate percentage of flagged invoices"""
        if self.total_invoices == 0:
            return 0.0
        return (self.flagged_count / self.total_invoices) * 100
    
    @property
    def approval_rate(self) -> float:
        """Calculate approval rate"""
        if self.total_invoices == 0:
            return 0.0
        return (self.approved_count / self.total_invoices) * 100
    
    def update_risk_score(self):
        """Update risk score based on statistics"""
        # Simple risk calculation based on flagged percentage
        flagged_pct = self.flagged_percentage
        
        if flagged_pct >= 50:
            self.risk_score = 80.0 + (flagged_pct - 50)
            self.risk_category = "high"
        elif flagged_pct >= 20:
            self.risk_score = 40.0 + (flagged_pct - 20)
            self.risk_category = "medium"
        else:
            self.risk_score = flagged_pct * 2
            self.risk_category = "low"
        
        # Adjust for blacklist
        if self.is_blacklisted:
            self.risk_score = 100.0
            self.risk_category = "high"
