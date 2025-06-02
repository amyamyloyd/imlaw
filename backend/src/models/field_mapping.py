"""Field mapping models"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class FieldMapping(BaseModel):
    """Model for field mapping between form fields and canonical fields"""
    form_field_id: str = Field(..., description="ID of the form field")
    canonical_field_id: str = Field(..., description="ID of the canonical field")
    confidence_score: float = Field(..., description="Confidence score of the mapping")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FieldMappingSuggestion(BaseModel):
    """Model for field mapping suggestions"""
    form_field_id: str = Field(..., description="ID of the form field")
    canonical_field_id: str = Field(..., description="ID of the canonical field")
    confidence_score: float = Field(..., description="Confidence score of the suggestion")
    similarity_score: float = Field(..., description="Text similarity score")
    context_score: float = Field(..., description="Context-based similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict) 