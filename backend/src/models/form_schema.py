from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from .repeatable_section import RepeatableSection

class FieldType(str, Enum):
    """Enumeration of supported field types"""
    TEXT = "Tx"  # Text field
    BUTTON = "Btn"  # Button (checkbox/radio)
    CHOICE = "Ch"  # Choice field (dropdown/listbox)
    DATE = "Dt"  # Date field
    CHECKBOX = "Cb"  # Checkbox field
    SELECT = "Sl"  # Select/dropdown field
    UNKNOWN = "Unknown"

class FieldFlags(BaseModel):
    """Field flags indicating field properties"""
    readonly: bool = False
    required: bool = False
    multiline: bool = False
    password: bool = False
    no_export: bool = False
    radio: bool = False
    pushbutton: bool = False
    combo: bool = False
    edit_combo: bool = False
    sort_combo: bool = False
    multiselect: bool = False
    commit_on_change: bool = False

class Position(BaseModel):
    """Model for field position on page"""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    width: float = Field(..., description="Field width")
    height: float = Field(..., description="Field height")

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Dimensions must be positive")
        return v

class ValidationRule(BaseModel):
    """Model for field validation rules"""
    rule_type: str = Field(..., description="Type of validation rule")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    error_message: str = Field(..., description="Error message for validation failure")

class FormFieldDefinition(BaseModel):
    """Model for form field definitions"""
    field_id: str = Field(..., description="Internal field ID in the PDF")
    field_type: FieldType = Field(..., description="Type of form field")
    field_name: str = Field(..., description="Name of the field in client data")
    label: str = Field(..., description="Display label for the field")
    position: Position = Field(..., description="Field position on page")
    page_number: int = Field(..., description="Page number where field appears")
    required: bool = Field(False, description="Whether field is required")
    validation_rules: List[ValidationRule] = Field(default_factory=list, description="Field validation rules")
    options: List[str] = Field(default_factory=list, description="Options for choice/select fields")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional field metadata")

    @field_validator("field_id")
    @classmethod
    def validate_field_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_id cannot be empty")
        return v

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_name cannot be empty")
        return v

    model_config = {
        "use_enum_values": True
    }

class FormMetadata(BaseModel):
    """Metadata for a PDF form"""
    id: str = Field(..., description="Unique identifier for the form")
    title: str = Field(..., min_length=1, description="Form title")
    description: Optional[str] = Field(None, description="Form description")
    form_type: str = Field(..., min_length=1, description="Type of form (e.g., i485, i130)")
    version: str = Field(..., min_length=1, description="Form version")
    pages: int = Field(..., gt=0, description="Number of pages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    fields: List[FormFieldDefinition] = Field(..., min_items=1, description="Form field definitions")
    total_fields: int = Field(..., gt=0, description="Total number of fields")
    author: Optional[str] = Field(None, description="Form author")
    keywords: List[str] = Field(default_factory=list, description="Form keywords/tags")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional form properties")

    @field_validator("total_fields")
    @classmethod
    def validate_total_fields(cls, v: int, info) -> int:
        if "fields" in info.data and len(info.data["fields"]) != v:
            raise ValueError("total_fields must match the number of fields")
        return v

    @field_validator("updated_at")
    @classmethod
    def validate_timestamps(cls, v: datetime, info) -> datetime:
        if "created_at" in info.data and v < info.data["created_at"]:
            raise ValueError("updated_at cannot be earlier than created_at")
        return v

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class FormSchema(BaseModel):
    """Schema for storing PDF form definitions."""
    form_type: str = Field(..., description="Form identifier (e.g., 'I-485')")
    version: str = Field(..., description="Form version")
    title: Optional[str] = Field(None, description="Form title")
    fields: List[FormFieldDefinition] = Field(..., description="List of form field definitions")
    total_fields: int = Field(..., description="Total number of fields in the form")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional form metadata")
    repeatable_sections: Dict[str, RepeatableSection] = Field(
        default_factory=dict,
        description="Dictionary of repeatable sections in the form"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "form_type": "I-485",
                    "version": "2023",
                    "title": "Application to Register Permanent Residence or Adjust Status",
                    "fields": [
                        {
                            "field_id": "Pt1Line1a_FamilyName[0]",
                            "field_type": "Tx",
                            "field_name": "Family Name (Last Name)",
                            "label": "Family Name (Last Name)",
                            "position": {"x": 100, "y": 200, "width": 200, "height": 30},
                            "page_number": 1,
                            "required": True,
                            "validation_rules": [],
                            "options": [],
                            "metadata": {}
                        }
                    ],
                    "total_fields": 1,
                    "metadata": {}
                }
            ]
        }
    } 