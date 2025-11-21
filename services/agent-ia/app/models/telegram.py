"""
Telegram models for bot integration
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    """Telegram user model"""
    id: int
    is_bot: bool = False
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    """Telegram chat model"""
    id: int
    type: str  # private, group, supergroup, channel
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramPhotoSize(BaseModel):
    """Telegram photo size model"""
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None


class TelegramDocument(BaseModel):
    """Telegram document model"""
    file_id: str
    file_unique_id: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class TelegramVoice(BaseModel):
    """Telegram voice message model"""
    file_id: str
    file_unique_id: str
    duration: int
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class TelegramMessage(BaseModel):
    """Telegram message model"""
    message_id: int
    from_user: Optional[TelegramUser] = Field(None, alias="from")
    chat: TelegramChat
    date: int
    text: Optional[str] = None
    photo: Optional[List[TelegramPhotoSize]] = None
    document: Optional[TelegramDocument] = None
    voice: Optional[TelegramVoice] = None
    caption: Optional[str] = None
    
    class Config:
        populate_by_name = True


class TelegramUpdate(BaseModel):
    """Telegram update model"""
    update_id: int
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None
    
    def get_message(self) -> Optional[TelegramMessage]:
        """Get the message from update"""
        return self.message or self.edited_message


class ProcessedTelegramMessage(BaseModel):
    """Processed Telegram message for internal use"""
    message_id: str
    chat_id: str
    user_id: str
    username: Optional[str]
    timestamp: datetime
    message_type: str  # text, photo, document, voice
    text_content: Optional[str] = None
    media_file_id: Optional[str] = None
    media_type: Optional[str] = None
    
    @classmethod
    def from_telegram_message(cls, msg: TelegramMessage) -> "ProcessedTelegramMessage":
        """Convert Telegram message to processed message"""
        message_type = "text"
        text_content = msg.text or msg.caption
        media_file_id = None
        media_type = None
        
        if msg.photo:
            message_type = "photo"
            media_file_id = msg.photo[-1].file_id  # Get largest photo
            media_type = "image"
        elif msg.document:
            message_type = "document"
            media_file_id = msg.document.file_id
            media_type = msg.document.mime_type or "application/octet-stream"
        elif msg.voice:
            message_type = "voice"
            media_file_id = msg.voice.file_id
            media_type = "audio"
        
        return cls(
            message_id=f"tg_{msg.message_id}",
            chat_id=str(msg.chat.id),
            user_id=str(msg.from_user.id) if msg.from_user else str(msg.chat.id),
            username=msg.from_user.username if msg.from_user else None,
            timestamp=datetime.fromtimestamp(msg.date),
            message_type=message_type,
            text_content=text_content,
            media_file_id=media_file_id,
            media_type=media_type
        )
