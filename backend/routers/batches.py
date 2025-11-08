"""
Batch router for batch creation and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.user import User
from models.batch import Batch, BatchStatus
from schemas.batch import (
    BatchResponse, BatchCreate, BatchUpdate, BatchDetailResponse,
    BatchListResponse, BatchStats
)
from dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_data: BatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new batch
    """
    batch = Batch(
        name=batch_data.name,
        description=batch_data.description,
        created_by=current_user.id,
        status=BatchStatus.CREATED
    )
    
    db.add(batch)
    db.commit()
    db.refresh(batch)
    
    return batch


@router.get("", response_model=BatchListResponse)
async def list_batches(
    status: Optional[BatchStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all batches with pagination
    """
    query = db.query(Batch)
    
    # Filter by status if provided
    if status:
        query = query.filter(Batch.status == status)
    
    # Filter by user (non-admins see only their batches)
    from models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Batch.created_by == current_user.id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    batches = query.order_by(Batch.created_at.desc()).offset(offset).limit(page_size).all()
    
    return BatchListResponse(
        items=batches,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{batch_id}", response_model=BatchDetailResponse)
async def get_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get batch details by ID
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Check access permission
    from models.user import UserRole
    if current_user.role != UserRole.ADMIN and batch.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this batch"
        )
    
    return batch


@router.put("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: int,
    batch_update: BatchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update batch information
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Check permission
    if batch.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to modify this batch"
        )
    
    # Update fields
    if batch_update.name:
        batch.name = batch_update.name
    
    if batch_update.description is not None:
        batch.description = batch_update.description
    
    if batch_update.status:
        batch.status = batch_update.status
    
    db.commit()
    db.refresh(batch)
    
    return batch


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a batch (and all associated invoices)
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Check permission
    from models.user import UserRole
    if current_user.role != UserRole.ADMIN and batch.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to delete this batch"
        )
    
    db.delete(batch)
    db.commit()
    
    return None


@router.get("/{batch_id}/status", response_model=BatchStats)
async def get_batch_status(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get batch processing status and statistics
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Update counts from database
    batch.update_counts(db)
    db.commit()
    
    return BatchStats(
        total_invoices=batch.total_invoices,
        processed_count=batch.processed_count,
        pending_count=batch.pending_count,
        flagged_count=batch.flagged_count,
        approved_count=batch.approved_count,
        rejected_count=batch.rejected_count,
        progress_percentage=batch.progress_percentage
    )
