"""
MinIO client for S3-compatible object storage
"""

from minio import Minio
from minio.error import S3Error
import logging
from typing import Optional, BinaryIO
from datetime import timedelta
from .config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO client wrapper for file storage operations"""
    
    def __init__(self):
        self.client: Optional[Minio] = None
        self.bucket_name = settings.minio_bucket_name
    
    def connect(self):
        """Connect to MinIO"""
        try:
            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure
            )
            
            # Create bucket if it doesn't exist
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            
            logger.info(f"Connected to MinIO at {settings.minio_endpoint}")
            
        except S3Error as e:
            logger.error(f"Failed to connect to MinIO: {str(e)}")
            raise
    
    def upload_file(self, file_data: BinaryIO, object_name: str, content_type: str = "application/octet-stream") -> str:
        """
        Upload file to MinIO
        
        Args:
            file_data: File data as binary stream
            object_name: Name of the object in MinIO
            content_type: MIME type of the file
            
        Returns:
            Object name in MinIO
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Seek back to start
            
            # Upload file
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_data,
                file_size,
                content_type=content_type
            )
            
            logger.info(f"Uploaded file: {object_name} ({file_size} bytes)")
            return object_name
            
        except S3Error as e:
            logger.error(f"Failed to upload file {object_name}: {str(e)}")
            raise
    
    def download_file(self, object_name: str) -> bytes:
        """
        Download file from MinIO
        
        Args:
            object_name: Name of the object in MinIO
            
        Returns:
            File data as bytes
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded file: {object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Failed to download file {object_name}: {str(e)}")
            raise
    
    def delete_file(self, object_name: str):
        """
        Delete file from MinIO
        
        Args:
            object_name: Name of the object in MinIO
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
            
        except S3Error as e:
            logger.error(f"Failed to delete file {object_name}: {str(e)}")
            raise
    
    def get_presigned_url(self, object_name: str, expires: timedelta = timedelta(hours=1)) -> str:
        """
        Get presigned URL for file download
        
        Args:
            object_name: Name of the object in MinIO
            expires: URL expiration time
            
        Returns:
            Presigned URL
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            
            logger.info(f"Generated presigned URL for: {object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {str(e)}")
            raise
    
    def file_exists(self, object_name: str) -> bool:
        """
        Check if file exists in MinIO
        
        Args:
            object_name: Name of the object in MinIO
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False


# Global MinIO client instance
minio_client = MinIOClient()
