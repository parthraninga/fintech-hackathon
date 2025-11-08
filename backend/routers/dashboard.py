"""
Dashboard router for analytics and metrics
"""
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from datetime import datetime, timedelta
import csv
import io

from database import get_db
from models.user import User
from models.invoice import Invoice, InvoiceStatus
from models.vendor import Vendor
from models.batch import Batch
from models.metrics import ModelMetrics
from schemas.dashboard import (
    DashboardMetrics, VendorRisk, ThroughputData,
    LatencyData, MetricFilter, ModelLearningMetrics
)
from dependencies import get_current_user
from utils.helpers import parse_date_range

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    vendor_ids: Optional[str] = Query(None),  # Comma-separated IDs
    batch_ids: Optional[str] = Query(None),  # Comma-separated IDs
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard KPI metrics
    """
    # Parse date range
    start_date, end_date = parse_date_range(start_date, end_date)
    
    # Base query
    query = db.query(Invoice).filter(
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date
    )
    
    # Apply filters
    if vendor_ids:
        vendor_id_list = [int(x) for x in vendor_ids.split(",")]
        query = query.filter(Invoice.vendor_id.in_(vendor_id_list))
    
    if batch_ids:
        batch_id_list = [int(x) for x in batch_ids.split(",")]
        query = query.filter(Invoice.batch_id.in_(batch_id_list))
    
    # Get all invoices for the period
    invoices = query.all()
    
    # Calculate metrics
    total_invoices = len(invoices)
    processed_invoices = sum(1 for inv in invoices if inv.is_completed)
    flagged_invoices = sum(1 for inv in invoices if inv.is_flagged)
    approved_invoices = sum(1 for inv in invoices if inv.status == InvoiceStatus.APPROVED)
    
    # Calculate rates
    time_diff_hours = (end_date - start_date).total_seconds() / 3600
    processing_rate = processed_invoices / time_diff_hours if time_diff_hours > 0 else 0
    
    # Calculate average latency
    processing_times = [inv.processing_time for inv in invoices if inv.processing_time > 0]
    avg_latency = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Calculate accuracy (from model metrics)
    latest_metric = db.query(ModelMetrics).order_by(ModelMetrics.created_at.desc()).first()
    accuracy_score = latest_metric.accuracy * 100 if latest_metric and latest_metric.accuracy else 0
    
    # Calculate percentages
    flagged_percentage = (flagged_invoices / total_invoices * 100) if total_invoices > 0 else 0
    approval_rate = (approved_invoices / processed_invoices * 100) if processed_invoices > 0 else 0
    
    # Calculate total amount
    total_amount = sum(inv.total_amount or 0 for inv in invoices)
    
    # Calculate trends (compare with previous period)
    previous_start = start_date - (end_date - start_date)
    previous_query = db.query(Invoice).filter(
        Invoice.created_at >= previous_start,
        Invoice.created_at < start_date
    )
    previous_invoices = previous_query.all()
    
    previous_total = len(previous_invoices)
    previous_flagged = sum(1 for inv in previous_invoices if inv.is_flagged)
    previous_latency = sum(inv.processing_time for inv in previous_invoices if inv.processing_time > 0)
    previous_latency_avg = previous_latency / len([inv for inv in previous_invoices if inv.processing_time > 0]) if len([inv for inv in previous_invoices if inv.processing_time > 0]) > 0 else 1
    
    invoices_trend = ((total_invoices - previous_total) / previous_total * 100) if previous_total > 0 else 0
    flagged_trend = ((flagged_invoices - previous_flagged) / previous_flagged * 100) if previous_flagged > 0 else 0
    latency_trend = ((avg_latency - previous_latency_avg) / previous_latency_avg * 100) if previous_latency_avg > 0 else 0
    
    return DashboardMetrics(
        total_invoices=total_invoices,
        processed_invoices=processed_invoices,
        flagged_invoices=flagged_invoices,
        processing_rate=round(processing_rate, 2),
        avg_latency=round(avg_latency, 2),
        accuracy_score=round(accuracy_score, 2),
        flagged_percentage=round(flagged_percentage, 2),
        approval_rate=round(approval_rate, 2),
        total_amount=round(total_amount, 2),
        invoices_trend=round(invoices_trend, 2),
        flagged_trend=round(flagged_trend, 2),
        latency_trend=round(latency_trend, 2)
    )


@router.get("/vendors", response_model=List[VendorRisk])
async def get_vendor_risks(
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("risk_score", regex="^(risk_score|flagged_count|total_amount)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get vendor risk analysis
    """
    # Query vendors with invoice data
    vendors = db.query(Vendor).filter(Vendor.total_invoices > 0)
    
    # Sort based on parameter
    if sort_by == "risk_score":
        vendors = vendors.order_by(Vendor.risk_score.desc())
    elif sort_by == "flagged_count":
        vendors = vendors.order_by(Vendor.flagged_count.desc())
    elif sort_by == "total_amount":
        vendors = vendors.order_by(Vendor.total_amount.desc())
    
    vendors = vendors.limit(limit).all()
    
    return [
        VendorRisk(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            gstin=vendor.gstin,
            risk_score=vendor.risk_score,
            risk_category=vendor.risk_category or "low",
            total_invoices=vendor.total_invoices,
            flagged_count=vendor.flagged_count,
            flagged_percentage=vendor.flagged_percentage,
            total_amount=vendor.total_amount,
            last_invoice_date=vendor.last_invoice_date
        )
        for vendor in vendors
    ]


@router.get("/throughput", response_model=List[ThroughputData])
async def get_throughput_data(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get agent throughput data
    """
    # Parse date range
    start_date, end_date = parse_date_range(start_date, end_date)
    
    # Mock data for different agent stages
    # In production, this would query actual agent performance metrics
    from models.invoice import AgentStage
    
    agent_data = []
    for stage in AgentStage:
        invoices = db.query(Invoice).filter(
            Invoice.current_stage == stage,
            Invoice.created_at >= start_date,
            Invoice.created_at <= end_date
        ).all()
        
        total = len(invoices)
        completed = sum(1 for inv in invoices if inv.is_completed)
        errors = sum(1 for inv in invoices if inv.status == InvoiceStatus.FAILED)
        
        avg_time = sum(inv.processing_time for inv in invoices if inv.processing_time) / total if total > 0 else 0
        success_rate = (completed / total * 100) if total > 0 else 0
        
        agent_data.append(
            ThroughputData(
                agent_name=stage.value.title(),
                invoices_processed=completed,
                avg_processing_time=round(avg_time, 2),
                success_rate=round(success_rate, 2),
                error_count=errors
            )
        )
    
    return agent_data


@router.get("/latency", response_model=List[LatencyData])
async def get_latency_distribution(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get latency distribution by stage
    """
    # Parse date range
    start_date, end_date = parse_date_range(start_date, end_date)
    
    # Mock latency data by stage
    # In production, this would calculate actual percentiles from timing data
    from models.invoice import AgentStage
    
    latency_data = []
    for stage in AgentStage:
        # Get processing times for this stage
        processing_times = db.query(Invoice.processing_time).filter(
            Invoice.current_stage == stage,
            Invoice.created_at >= start_date,
            Invoice.created_at <= end_date,
            Invoice.processing_time.isnot(None)
        ).all()
        
        times = [t[0] for t in processing_times if t[0]]
        
        if times:
            times.sort()
            n = len(times)
            
            avg_latency = sum(times) / n
            p50 = times[n // 2]
            p95 = times[int(n * 0.95)] if n > 20 else times[-1]
            p99 = times[int(n * 0.99)] if n > 100 else times[-1]
            max_latency = max(times)
        else:
            avg_latency = p50 = p95 = p99 = max_latency = 0
        
        latency_data.append(
            LatencyData(
                stage=stage.value,
                avg_latency=round(avg_latency, 2),
                p50=round(p50, 2),
                p95=round(p95, 2),
                p99=round(p99, 2),
                max_latency=round(max_latency, 2)
            )
        )
    
    return latency_data


@router.get("/model/metrics", response_model=ModelLearningMetrics)
async def get_model_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get model learning and performance metrics
    """
    latest_metric = db.query(ModelMetrics).order_by(ModelMetrics.created_at.desc()).first()
    
    if not latest_metric:
        # Return default metrics if none exist
        return ModelLearningMetrics(
            model_version="v1.0.0",
            accuracy=0.0,
            feedback_queue_length=0,
            retrain_count=0,
            is_production_ready=False
        )
    
    return ModelLearningMetrics(
        model_version=latest_metric.model_version,
        accuracy=latest_metric.accuracy or 0.0,
        precision=latest_metric.precision,
        recall=latest_metric.recall,
        f1_score=latest_metric.f1_score,
        feedback_queue_length=latest_metric.feedback_queue_length,
        retrain_count=latest_metric.retrain_count,
        last_retrain=latest_metric.last_retrain,
        is_production_ready=latest_metric.is_production_ready
    )


@router.get("/export/csv")
async def export_dashboard_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export dashboard data to CSV
    """
    # Parse date range
    start_date, end_date = parse_date_range(start_date, end_date)
    
    # Get invoices
    invoices = db.query(Invoice).filter(
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date
    ).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Invoice ID", "Invoice Number", "Vendor Name", "GSTIN",
        "Total Amount", "Status", "Is Flagged", "Created At", "Processed At"
    ])
    
    # Write data
    for inv in invoices:
        writer.writerow([
            inv.id,
            inv.invoice_number or "",
            inv.vendor_name or "",
            inv.vendor_gstin or "",
            inv.total_amount or 0,
            inv.status.value,
            "Yes" if inv.is_flagged else "No",
            inv.created_at.isoformat(),
            inv.processed_at.isoformat() if inv.processed_at else ""
        ])
    
    # Return CSV response
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )
