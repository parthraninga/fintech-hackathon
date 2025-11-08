"""
File validation utilities
"""
import os
from typing import List
from fastapi import UploadFile, HTTPException, status
from config import settings

# Try to import magic, but make it optional
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


def validate_file_size(file: UploadFile):
    """
    Validate file size against maximum allowed size
    """
    # Read file to get size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {file_size} exceeds maximum allowed size {settings.MAX_UPLOAD_SIZE}"
        )
    
    return file_size


def validate_file_extension(filename: str, allowed_extensions: List[str] = None):
    """
    Validate file extension
    """
    if allowed_extensions is None:
        allowed_extensions = settings.ALLOWED_EXTENSIONS
    
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension {file_ext} not allowed. Allowed: {', '.join(allowed_extensions)}"
        )
    
    return file_ext


def validate_file_type(file: UploadFile):
    """
    Validate file type using magic numbers (more secure than extension)
    """
    if not HAS_MAGIC:
        # Fallback: just check content type from upload
        allowed_content_types = [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/jpg"
        ]
        if file.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed"
            )
        return file.content_type
    
    # Read first 2048 bytes for magic number detection
    file.file.seek(0)
    file_header = file.file.read(2048)
    file.file.seek(0)
    
    # Detect MIME type
    mime_type = magic.from_buffer(file_header, mime=True)
    
    # Allowed MIME types
    allowed_mimes = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg"
    ]
    
    if mime_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {mime_type} not allowed"
        )
    
    return mime_type


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


async def save_upload_file(file: UploadFile, destination: str) -> str:
    """
    Save uploaded file to disk
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    # Save file
    with open(destination, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return destination
