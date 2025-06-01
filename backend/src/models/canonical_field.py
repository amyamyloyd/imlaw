from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class DataType(str, Enum):
    """Supported data types for canonical fields"""
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    
class ValidationRule(BaseModel):
    """Validation rule definition"""
    rule_type: str = Field(..., description="Type of validation rule")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    error_message: Optional[str] = Field(None, description="Custom error message")

class ValidationHistory(BaseModel):
    """Track changes to validation rules"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    changed_by: str = Field(..., description="User who made the change")
    previous_rules: List[ValidationRule] = Field(default_factory=list)
    new_rules: List[ValidationRule] = Field(default_factory=list)
    reason: Optional[str] = Field(None, description="Reason for change")

class UsageStats(BaseModel):
    """Track field usage statistics"""
    total_uses: int = Field(default=0, description="Number of times field has been used")
    last_used: Optional[datetime] = Field(None, description="Last time field was used")
    form_usage: Dict[str, int] = Field(default_factory=dict, description="Usage count by form type")
    error_count: int = Field(default=0, description="Number of validation errors")

class FormFieldMapping(BaseModel):
    """Mapping between a canonical field and a specific form field"""
    form_type: str = Field(..., description="Form identifier (e.g., 'I-485')")
    form_version: str = Field(..., description="Form version")
    field_id: str = Field(..., description="Internal PDF field ID in the form")
    mapping_type: str = Field("direct", description="Type of mapping (direct, transform, composite)")
    transform_logic: Optional[str] = Field(None, description="Logic for transforming data if needed")
    notes: Optional[str] = Field(None, description="Additional mapping notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("form_type")
    def validate_form_type(cls, v):
        if not v.strip():
            raise ValueError("form_type cannot be empty")
        return v.upper()

    @validator("form_version")
    def validate_form_version(cls, v):
        if not v.strip():
            raise ValueError("form_version cannot be empty")
        return v

class CanonicalField(BaseModel):
    """Schema for canonical field definitions in the registry"""
    field_name: str = Field(..., description="Unique identifier for the canonical field")
    display_name: str = Field(..., description="Human-readable field name")
    description: Optional[str] = Field(None, description="Field description")
    data_type: DataType = Field(..., description="Data type (string, number, date, etc.)")
    validation_rules: List[ValidationRule] = Field(default_factory=list, description="Validation rules")
    form_mappings: List[FormFieldMapping] = Field(default_factory=list, description="Mappings to form fields")
    category: Optional[str] = Field(None, description="Field category (personal, address, etc.)")
    required: bool = Field(False, description="Whether this field is typically required")
    parent_field: Optional[str] = Field(None, description="Parent field for hierarchical relationships")
    group_name: Optional[str] = Field(None, description="Logical group this field belongs to")
    dependencies: List[str] = Field(default_factory=list, description="Fields this field depends on")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    aliases: List[str] = Field(default_factory=list, description="Alternative names for this field")
    source_priority: List[str] = Field(default_factory=list, description="Preferred data sources in priority order")
    validation_history: List[ValidationHistory] = Field(default_factory=list, description="History of validation rule changes")
    usage_stats: UsageStats = Field(default_factory=UsageStats, description="Field usage statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator("field_name")
    def validate_field_name(cls, v):
        if not v.strip():
            raise ValueError("field_name cannot be empty")
        if not v.replace("_", "").isalnum():
            raise ValueError("field_name must contain only alphanumeric characters and underscores")
        return v.lower()

    @validator("display_name")
    def validate_display_name(cls, v):
        if not v.strip():
            raise ValueError("display_name cannot be empty")
        return v

    @validator("dependencies")
    def validate_dependencies(cls, v, values):
        if "field_name" in values and values["field_name"] in v:
            raise ValueError("field cannot depend on itself")
        return v

    @validator("updated_at")
    def validate_updated_at(cls, v, values):
        if "created_at" in values and v < values["created_at"]:
            raise ValueError("updated_at cannot be before created_at")
        return v

    class Config:
        schema_extra = {
            "example": {
                "field_name": "family_name",
                "display_name": "Family Name",
                "description": "Legal family name/surname",
                "data_type": "string",
                "validation_rules": [
                    {
                        "rule_type": "length",
                        "parameters": {
                            "min": 1,
                            "max": 50
                        },
                        "error_message": "Family name must be between 1 and 50 characters"
                    },
                    {
                        "rule_type": "pattern",
                        "parameters": {
                            "regex": "^[A-Za-z\\s\\-']+$"
                        },
                        "error_message": "Family name can only contain letters, spaces, hyphens, and apostrophes"
                    }
                ],
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
                "group_name": "name",
                "aliases": ["surname", "last_name"],
                "source_priority": ["passport", "birth_certificate"],
                "metadata": {
                    "sensitivity": "high",
                    "verification_required": True
                }
            }
        } 