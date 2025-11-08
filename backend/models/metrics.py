"""
Model metrics for tracking ML model performance
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from datetime import datetime
from database import Base


class ModelMetrics(Base):
    """Model metrics model"""
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Model information
    model_version = Column(String(50), nullable=False, index=True)
    model_type = Column(String(100))  # "ocr", "extraction", "validation", etc.
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    
    # Training data
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    test_samples = Column(Integer)
    
    # Feedback & Learning
    feedback_queue_length = Column(Integer, default=0)
    retrain_count = Column(Integer, default=0)
    last_retrain = Column(DateTime)
    
    # Latency metrics (in milliseconds)
    avg_latency = Column(Float)
    p50_latency = Column(Float)
    p95_latency = Column(Float)
    p99_latency = Column(Float)
    
    # Additional metrics (JSON)
    additional_metrics = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ModelMetrics {self.model_version} - Accuracy: {self.accuracy}>"
    
    @property
    def is_production_ready(self) -> bool:
        """Check if model meets production quality thresholds"""
        if not self.accuracy:
            return False
        return self.accuracy >= 0.90 and (self.f1_score or 0) >= 0.85
