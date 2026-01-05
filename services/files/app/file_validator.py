"""
File validation utilities
"""

import os
import magic
import logging
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException
from .config import settings

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass


class FileValidator:
    """Validates uploaded files"""
    
    @staticmethod
    def validate_file_size(file: UploadFile) -> bool:
        """
        Validate file size
        
        Args:
            file: Uploaded file
            
        Returns:
            True if valid
            
        Raises:
            FileValidationError: If file is too large
        """
        # Read file to get size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Seek back to start
        
        if file_size > settings.max_file_size_bytes:
            raise FileValidationError(
                f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size "
                f"({settings.max_file_size_mb} MB)"
            )
        
        logger.debug(f"File size validation passed: {file_size} bytes")
        return True
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """
        Validate file extension
        
        Args:
            filename: Name of the file
            
        Returns:
            True if valid
            
        Raises:
            FileValidationError: If extension is not allowed
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if ext not in settings.allowed_extensions_list:
            raise FileValidationError(
                f"File extension '{ext}' is not allowed. "
                f"Allowed extensions: {', '.join(settings.allowed_extensions_list)}"
            )
        
        logger.debug(f"File extension validation passed: {ext}")
        return True
    
    @staticmethod
    def validate_file_type(file: UploadFile) -> bool:
        """
        Validate file MIME type using python-magic
        
        Args:
            file: Uploaded file
            
        Returns:
            True if valid
            
        Raises:
            FileValidationError: If MIME type is not allowed
        """
        try:
            # Read first 2048 bytes for magic detection
            file.file.seek(0)
            file_header = file.file.read(2048)
            file.file.seek(0)
            
            # Detect MIME type
            mime = magic.from_buffer(file_header, mime=True)
            
            # Allowed MIME types for Excel and CSV
            allowed_mimes = [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
                'application/vnd.ms-excel',  # .xls
                'text/csv',  # .csv
                'text/plain',  # .csv (sometimes detected as plain text)
                'application/octet-stream'  # Generic binary (fallback)
            ]
            
            if mime not in allowed_mimes:
                raise FileValidationError(
                    f"File type '{mime}' is not allowed. "
                    f"Expected Excel or CSV file."
                )
            
            logger.debug(f"File type validation passed: {mime}")
            return True
            
        except Exception as e:
            logger.warning(f"Could not validate file type: {str(e)}")
            # Don't fail validation if magic detection fails
            return True
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate filename for security
        
        Args:
            filename: Name of the file
            
        Returns:
            True if valid
            
        Raises:
            FileValidationError: If filename is invalid
        """
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise FileValidationError("Invalid filename: path traversal detected")
        
        # Check for empty filename
        if not filename or filename.strip() == '':
            raise FileValidationError("Filename cannot be empty")
        
        # Check filename length
        if len(filename) > 255:
            raise FileValidationError("Filename is too long (max 255 characters)")
        
        logger.debug(f"Filename validation passed: {filename}")
        return True
    
    @classmethod
    def validate_file(cls, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Perform all file validations
        
        Args:
            file: Uploaded file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            cls.validate_filename(file.filename)
            cls.validate_file_extension(file.filename)
            cls.validate_file_size(file)
            cls.validate_file_type(file)
            
            return True, None
            
        except FileValidationError as e:
            logger.warning(f"File validation failed: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error during file validation: {str(e)}")
            return False, f"Validation error: {str(e)}"


# Global file validator instance
file_validator = FileValidator()
