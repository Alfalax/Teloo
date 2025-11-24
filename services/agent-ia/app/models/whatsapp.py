"""
WhatsApp webhook data models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class WhatsAppContact(BaseModel):
    """WhatsApp contact information"""
    profile: Optional[Dict[str, str]] = None
    wa_id: str


class WhatsAppMessage(BaseModel):
    """WhatsApp message model"""
    id: str
    from_: str = Field(alias="from")
    timestamp: str
    type: str
    text: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    audio: Optional[Dict[str, str]] = None
    document: Optional[Dict[str, str]] = None
    video: Optional[Dict[str, str]] = None
    voice: Optional[Dict[str, str]] = None
    context: Optional[Dict[str, Any]] = None


class WhatsAppChange(BaseModel):
    """WhatsApp webhook change"""
    value: Dict[str, Any]
    field: str


class WhatsAppEntry(BaseModel):
    """WhatsApp webhook entry"""
    id: str
    changes: List[WhatsAppChange]


class WhatsAppWebhook(BaseModel):
    """WhatsApp webhook payload"""
    object: str
    entry: List[WhatsAppEntry]


class ProcessedMessage(BaseModel):
    """Processed WhatsApp message"""
    message_id: str
    from_number: str
    timestamp: datetime
    message_type: str
    text_content: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    context_message_id: Optional[str] = None
    
    def is_text_message(self) -> bool:
        """Check if message contains text"""
        return self.message_type == "text" and bool(self.text_content)
    
    def is_media_message(self) -> bool:
        """Check if message contains media"""
        return self.media_url is not None
    
    def is_audio_message(self) -> bool:
        """Check if message is audio/voice"""
        return self.media_type in ["audio", "voice"]
    
    def is_document_message(self) -> bool:
        """Check if message is a document"""
        return self.media_type == "document"


class WhatsAppOutgoingMessage(BaseModel):
    """Outgoing WhatsApp message"""
    messaging_product: str = "whatsapp"
    to: str
    type: str = "text"
    text: Optional[Dict[str, str]] = None
    template: Optional[Dict[str, Any]] = None


class RateLimitInfo(BaseModel):
    """Rate limit information"""
    ip_address: str
    request_count: int
    window_start: datetime
    is_limited: bool = False