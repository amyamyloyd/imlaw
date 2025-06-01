from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class FormFieldMapping(BaseModel):
    """Mapping between a canonical field and a specific form field."""
    form_type: str = Field(..., description="Form identifier (e.g., 'I-485')")
    form_version: str = Field(..., description="Form version")
    field_id: str = Field(..., description="Internal PDF field ID in the form")
    mapping_type: str = Field("direct", description="Type of mapping (direct, transform, composite)")
    transform_logic: Optional[str] = Field(None, description="Logic for transforming data if needed")
    notes: Optional[str] = Field(None, description="Additional mapping notes")

class CanonicalField(BaseModel):
    """Schema for canonical field definitions in the registry."""
    field_name: str = Field(..., description="Unique identifier for the canonical field")
    display_name: str = Field(..., description="Human-readable field name")
    description: Optional[str] = Field(None, description="Field description")
    data_type: str = Field(..., description="Data type (string, number, date, boolean, etc.)")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules")
    form_mappings: List[FormFieldMapping] = Field(default_factory=list, description="Mappings to form fields")
    category: Optional[str] = Field(None, description="Field category (personal, address, etc.)")
    required: bool = Field(False, description="Whether this field is typically required")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "field_name": "family_name",
                "display_name": "Family Name",
                "description": "Legal family name/surname",
                "data_type": "string",
                "validation_rules": {
                    "min_length": 1,
                    "max_length": 50,
                    "pattern": "^[A-Za-z\\s\\-']+$"
                },
                "form_mappings": [
                    {
                        "form_type": "I-485",
                        "form_version": "10/15/2023",
                        "field_id": "form1[0].#subform[0].TextField1[0]",
                        "mapping_type": "direct"
                    }
                ],
                "category": "personal",
                "required": True,
                "metadata": {
                    "aliases": ["surname", "last_name"],
                    "source_priority": ["passport", "birth_certificate"]
                }
            }
        } 