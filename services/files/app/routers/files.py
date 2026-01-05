"""
File upload/download endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional
import uuid
import os
import io
import logging
from datetime import timedelta

from ..config import settings
from ..minio_client import minio_client
from ..file_validator import file_validator, FileValidationError
from ..antivirus import antivirus_scanner, AntivirusError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = Query(None, description="Optional folder path in storage")
):
    """
    Upload a file to MinIO storage
    
    - Validates file format, size, and type
    - Scans for viruses (if ClamAV is enabled)
    - Stores in MinIO
    
    Returns file ID and download URL
    """
    try:
        # Validate file
        is_valid, error_message = file_validator.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Read file data
        file_data = await file.read()
        
        # Scan for viruses
        is_clean, virus_name = antivirus_scanner.scan_file(file_data)
        if not is_clean:
            logger.warning(f"Virus detected in uploaded file: {virus_name}")
            raise HTTPException(
                status_code=400,
                detail=f"File contains virus: {virus_name}"
            )
        
        # Generate unique object name
        file_id = str(uuid.uuid4())
        _, ext = os.path.splitext(file.filename)
        
        if folder:
            object_name = f"{folder}/{file_id}{ext}"
        else:
            object_name = f"{file_id}{ext}"
        
        # Upload to MinIO
        file_stream = io.BytesIO(file_data)
        minio_client.upload_file(
            file_stream,
            object_name,
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Generate presigned URL for download
        download_url = minio_client.get_presigned_url(object_name, expires=timedelta(hours=24))
        
        logger.info(f"File uploaded successfully: {object_name}")
        
        return {
            "success": True,
            "file_id": file_id,
            "object_name": object_name,
            "original_filename": file.filename,
            "size_bytes": len(file_data),
            "download_url": download_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/download/{object_name:path}")
async def download_file(object_name: str):
    """
    Download a file from MinIO storage
    
    Returns file as streaming response
    """
    try:
        # Check if file exists
        if not minio_client.file_exists(object_name):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Download file
        file_data = minio_client.download_file(object_name)
        
        # Get filename from object name
        filename = os.path.basename(object_name)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@router.get("/url/{object_name:path}")
async def get_download_url(
    object_name: str,
    expires_hours: int = Query(1, ge=1, le=168, description="URL expiration in hours (1-168)")
):
    """
    Get presigned download URL for a file
    
    Returns temporary URL that expires after specified hours
    """
    try:
        # Check if file exists
        if not minio_client.file_exists(object_name):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generate presigned URL
        url = minio_client.get_presigned_url(
            object_name,
            expires=timedelta(hours=expires_hours)
        )
        
        return {
            "success": True,
            "object_name": object_name,
            "download_url": url,
            "expires_in_hours": expires_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")


@router.delete("/{object_name:path}")
async def delete_file(object_name: str):
    """
    Delete a file from MinIO storage
    """
    try:
        # Check if file exists
        if not minio_client.file_exists(object_name):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete file
        minio_client.delete_file(object_name)
        
        logger.info(f"File deleted successfully: {object_name}")
        
        return {
            "success": True,
            "message": "File deleted successfully",
            "object_name": object_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/templates/ofertas")
async def download_ofertas_template():
    """
    Download Excel template for ofertas masivas
    
    Returns pre-configured Excel template
    """
    # This would return a pre-made template file
    # For now, return a simple response
    return {
        "message": "Template download endpoint",
        "template_name": "ofertas_template.xlsx",
        "note": "Template file should be stored in MinIO and downloaded here"
    }
