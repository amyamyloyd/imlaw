from enum import Enum
from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

class DocumentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class DocumentMetadata(BaseModel):
    """Additional metadata for a document"""
    document_type: str
    description: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    content_type: str
    file_size: int
    original_filename: str
    custom_metadata: Optional[Dict] = None

class DocumentResponse(BaseModel):
    """Response model for document operations"""
    id: str
    client_id: str
    status: DocumentStatus
    metadata: DocumentMetadata
    status_reason: Optional[str] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 