"""
Dashboard schemas for analytics and metrics
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MetricFilter(BaseModel):
    """Schema for dashboard metric filtering"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    vendor_ids: Optional[List[int]] = None
    batch_ids: Optional[List[int]] = None


class DashboardMetrics(BaseModel):
    """Schema for dashboard KPI metrics"""
    total_invoices: int
    processed_invoices: int
    flagged_invoices: int
    processing_rate: float  # invoices per hour
    avg_latency: float  # seconds
    accuracy_score: float  # 0-100
    flagged_percentage: float
    approval_rate: float
    total_amount: float
    
    # Trend data (vs previous period)
    invoices_trend: float  # percentage change
    flagged_trend: float
    latency_trend: float


class VendorRisk(BaseModel):
    """Schema for vendor risk data"""
    vendor_id: int
    vendor_name: str
    gstin: str
    risk_score: float
    risk_category: str
    total_invoices: int
    flagged_count: int
    flagged_percentage: float
    total_amount: float
    last_invoice_date: Optional[datetime] = None


class ThroughputData(BaseModel):
    """Schema for agent throughput data"""
    agent_name: str
    invoices_processed: int
    avg_processing_time: float  # seconds
    success_rate: float  # percentage
    error_count: int


class LatencyData(BaseModel):
    """Schema for latency distribution"""
    stage: str
    avg_latency: float
    p50: float
    p95: float
    p99: float
    max_latency: float


class ExportRequest(BaseModel):
    """Schema for CSV export request"""
    filters: Optional[MetricFilter] = None
    include_fields: Optional[List[str]] = None
    format: str = Field("csv", pattern="^(csv|xlsx)$")


class ModelLearningMetrics(BaseModel):
    """Schema for model learning metrics"""
    model_version: str
    accuracy: float
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    feedback_queue_length: int
    retrain_count: int
    last_retrain: Optional[datetime] = None
    is_production_ready: bool
