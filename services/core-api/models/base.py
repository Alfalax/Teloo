"""
Base model class for all TeLOO V3 models
"""

from tortoise.models import Model
from tortoise import fields
import uuid
from datetime import datetime


class BaseModel(Model):
    """
    Base model class with common fields for all models
    """
    
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        abstract = True
        
    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"
        
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.id}>"