"""
Antivirus scanning using ClamAV
"""

import pyclamd
import logging
from typing import Tuple, Optional
from .config import settings

logger = logging.getLogger(__name__)


class AntivirusError(Exception):
    """Custom exception for antivirus errors"""
    pass


class AntivirusScanner:
    """Scans files for viruses using ClamAV"""
    
    def __init__(self):
        self.client: Optional[pyclamd.ClamdNetworkSocket] = None
        self.enabled = settings.clamav_enabled
    
    def connect(self):
        """Connect to ClamAV daemon"""
        if not self.enabled:
            logger.info("ClamAV is disabled, skipping antivirus scanning")
            return
        
        try:
            self.client = pyclamd.ClamdNetworkSocket(
                host=settings.clamav_host,
                port=settings.clamav_port
            )
            
            # Test connection
            if not self.client.ping():
                raise AntivirusError("ClamAV daemon is not responding")
            
            logger.info(f"Connected to ClamAV at {settings.clamav_host}:{settings.clamav_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ClamAV: {str(e)}")
            # Don't raise error, just disable scanning
            self.enabled = False
            logger.warning("ClamAV scanning disabled due to connection failure")
    
    def scan_file(self, file_data: bytes) -> Tuple[bool, Optional[str]]:
        """
        Scan file for viruses
        
        Args:
            file_data: File data as bytes
            
        Returns:
            Tuple of (is_clean, virus_name)
            - (True, None) if file is clean
            - (False, virus_name) if virus detected
        """
        if not self.enabled:
            logger.debug("Antivirus scanning is disabled, skipping")
            return True, None
        
        if not self.client:
            logger.warning("ClamAV client not connected, skipping scan")
            return True, None
        
        try:
            # Scan file data
            result = self.client.scan_stream(file_data)
            
            if result is None:
                # No virus detected
                logger.debug("File scan completed: clean")
                return True, None
            else:
                # Virus detected
                virus_name = result.get('stream', ['UNKNOWN'])[1]
                logger.warning(f"Virus detected: {virus_name}")
                return False, virus_name
                
        except Exception as e:
            logger.error(f"Error during virus scan: {str(e)}")
            # Don't fail upload if scanning fails
            logger.warning("Continuing without virus scan due to error")
            return True, None
    
    def get_version(self) -> Optional[str]:
        """Get ClamAV version"""
        if not self.enabled or not self.client:
            return None
        
        try:
            return self.client.version()
        except Exception as e:
            logger.error(f"Failed to get ClamAV version: {str(e)}")
            return None


# Global antivirus scanner instance
antivirus_scanner = AntivirusScanner()
