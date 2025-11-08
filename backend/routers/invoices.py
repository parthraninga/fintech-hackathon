"""
Invoice router for invoice upload, processing, and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime
import os

from database import get_db
from models.user import User
from models.invoice import Invoice, InvoiceStatus, AgentStage
from models.batch import Batch
from models.vendor import Vendor
from schemas.invoice import (
    InvoiceResponse, InvoiceCreate, InvoiceUpdate, InvoiceFilter,
    InvoiceStatusUpdate, InvoiceListResponse, InvoiceDetailResponse
)
from dependencies import get_current_user
from utils.validators import (
    validate_file_size, validate_file_extension,
    validate_file_type, sanitize_filename, save_upload_file
)
from utils.helpers import generate_unique_filename, get_file_path

router = APIRouter()


@router.post("/upload", response_model=List[InvoiceResponse], status_code=status.HTTP_201_CREATED)
async def upload_invoices(
    batch_id: int = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload one or more invoice files
    """
    # Verify batch exists and user has access
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    if batch.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this batch"
        )
    
    uploaded_invoices = []
    
    for file in files:
        # Validate file
        file_size = validate_file_size(file)
        file_ext = validate_file_extension(file.filename)
        mime_type = validate_file_type(file)
        
        # Generate unique filename
        safe_filename = sanitize_filename(file.filename)
        unique_filename = generate_unique_filename(safe_filename)
        file_path = get_file_path(batch_id, unique_filename)
        
        # Save file
        await save_upload_file(file, file_path)
        
        # Create invoice record
        invoice = Invoice(
            batch_id=batch_id,
            filename=safe_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=mime_type,
            status=InvoiceStatus.PENDING,
            current_stage=AgentStage.UPLOAD
        )
        
        db.add(invoice)
        uploaded_invoices.append(invoice)
    
    # Update batch counts
    batch.total_invoices += len(files)
    batch.pending_count += len(files)
    
    db.commit()
    
    # Refresh all invoices
    for invoice in uploaded_invoices:
        db.refresh(invoice)
    
    # Trigger OCR processing for each uploaded invoice
    from services.invoice_processing import process_invoice_async
    import asyncio
    
    # Start background processing for each invoice
    for invoice in uploaded_invoices:
        print(f"🚀 Starting OCR processing for invoice {invoice.id}: {invoice.filename}")
        # Create background task (non-blocking)
        asyncio.create_task(process_invoice_async(invoice.id))
    
    return uploaded_invoices


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    batch_id: Optional[int] = Query(None),
    vendor_id: Optional[int] = Query(None),
    status: Optional[InvoiceStatus] = Query(None),
    is_flagged: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List invoices with filtering and pagination
    """
    query = db.query(Invoice)
    
    # Apply filters
    if batch_id:
        query = query.filter(Invoice.batch_id == batch_id)
    
    if vendor_id:
        query = query.filter(Invoice.vendor_id == vendor_id)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    if is_flagged is not None:
        query = query.filter(Invoice.is_flagged == is_flagged)
    
    if search:
        query = query.filter(
            or_(
                Invoice.invoice_number.ilike(f"%{search}%"),
                Invoice.vendor_name.ilike(f"%{search}%"),
                Invoice.filename.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    invoices = query.order_by(Invoice.created_at.desc()).offset(offset).limit(page_size).all()
    
    return InvoiceListResponse(
        items=invoices,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get invoice details by ID
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update invoice data
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Update fields
    if invoice_update.status:
        invoice.status = invoice_update.status
    
    if invoice_update.current_stage:
        invoice.current_stage = invoice_update.current_stage
    
    if invoice_update.progress_percentage is not None:
        invoice.progress_percentage = invoice_update.progress_percentage
    
    if invoice_update.extracted_data:
        invoice.extracted_data = invoice_update.extracted_data
    
    if invoice_update.is_flagged is not None:
        invoice.is_flagged = invoice_update.is_flagged
    
    if invoice_update.flag_reasons:
        invoice.flag_reasons = invoice_update.flag_reasons
    
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.post("/{invoice_id}/approve", response_model=InvoiceResponse)
async def approve_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve an invoice
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    invoice.status = InvoiceStatus.APPROVED
    invoice.approved_at = datetime.utcnow()
    
    # Update vendor stats
    if invoice.vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == invoice.vendor_id).first()
        if vendor:
            vendor.approved_count += 1
            vendor.update_risk_score()
    
    # Update batch stats
    batch = db.query(Batch).filter(Batch.id == invoice.batch_id).first()
    if batch:
        batch.approved_count += 1
        batch.update_counts(db)
    
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.post("/{invoice_id}/reject", response_model=InvoiceResponse)
async def reject_invoice(
    invoice_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject an invoice
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    invoice.status = InvoiceStatus.REJECTED
    invoice.rejected_at = datetime.utcnow()
    
    if reason:
        if not invoice.flag_reasons:
            invoice.flag_reasons = []
        invoice.flag_reasons.append(reason)
    
    # Update vendor stats
    if invoice.vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == invoice.vendor_id).first()
        if vendor:
            vendor.rejected_count += 1
            vendor.update_risk_score()
    
    # Update batch stats
    batch = db.query(Batch).filter(Batch.id == invoice.batch_id).first()
    if batch:
        batch.rejected_count += 1
        batch.update_counts(db)
    
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an invoice
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Delete file from disk
    if os.path.exists(invoice.file_path):
        os.remove(invoice.file_path)
    
    db.delete(invoice)
    db.commit()
    
    return None
