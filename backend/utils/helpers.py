"""
Helper utility functions
"""
import os
import uuid
from datetime import datetime
from typing import Optional


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate unique filename using UUID
    """
    name, ext = os.path.splitext(original_filename)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


def get_file_path(batch_id: int, filename: str) -> str:
    """
    Generate file storage path
    """
    from config import settings
    
    # Organize by batch and date
    date_str = datetime.now().strftime("%Y/%m/%d")
    file_dir = os.path.join(settings.UPLOAD_DIR, f"batch_{batch_id}", date_str)
    
    return os.path.join(file_dir, filename)


def calculate_progress(current: int, total: int) -> float:
    """
    Calculate progress percentage
    """
    if total == 0:
        return 0.0
    return round((current / total) * 100, 2)


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable size
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def parse_date_range(start_date: Optional[datetime], end_date: Optional[datetime]):
    """
    Parse and validate date range
    """
    if start_date and end_date:
        if start_date > end_date:
            raise ValueError("start_date must be before end_date")
    
    if not start_date:
        # Default to 30 days ago
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=30)
    
    if not end_date:
        end_date = datetime.utcnow()
    
    return start_date, end_date
