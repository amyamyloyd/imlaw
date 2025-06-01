from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, constr, validator
from enum import Enum

class FieldType(str, Enum):
    """Enumeration of supported field types"""
    TEXT = "Tx"  # Text field
    BUTTON = "Btn"  # Button (checkbox/radio)
    CHOICE = "Ch"  # Choice field (dropdown/listbox)
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
    """Field position on the page"""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    width: float = Field(..., description="Field width")
    height: float = Field(..., description="Field height")

    @validator("width", "height")
    def validate_dimensions(cls, v):
        if v <= 0:
            raise ValueError("Dimensions must be positive")
        return v

class FormFieldDefinition(BaseModel):
    """Definition of a single form field"""
    field_id: str = Field(..., description="Unique identifier for the field within the form")
    field_type: FieldType = Field(..., description="Type of form field")
    field_name: str = Field(..., description="Display name of the field")
    field_value: Optional[str] = Field(None, description="Current or default value")
    position: Position = Field(..., description="Field position information")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional field properties")
    tooltip: Optional[str] = Field(None, description="Field tooltip/help text")
    label: Optional[str] = Field(None, description="Field label text")
    page_number: Optional[int] = Field(None, ge=1, description="Page number where field appears")
    parent_field: Optional[str] = Field(None, description="ID of parent field if nested")
    child_fields: List[str] = Field(default_factory=list, description="IDs of child fields")
    flags: FieldFlags = Field(default_factory=FieldFlags, description="Field flags/properties")

    @validator("field_id")
    def validate_field_id(cls, v):
        if not v.strip():
            raise ValueError("field_id cannot be empty")
        return v

    @validator("field_name")
    def validate_field_name(cls, v):
        if not v.strip():
            raise ValueError("field_name cannot be empty")
        return v

    class Config:
        use_enum_values = True

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

    @validator("total_fields")
    def validate_total_fields(cls, v, values):
        if "fields" in values and len(values["fields"]) != v:
            raise ValueError("total_fields must match the number of fields")
        return v

    @validator("updated_at")
    def validate_timestamps(cls, v, values):
        if "created_at" in values and v < values["created_at"]:
            raise ValueError("updated_at cannot be earlier than created_at")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
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

    class Config:
        schema_extra = {
            "example": {
                "form_type": "I-485",
                "version": "10/15/2023",
                "title": "Application to Register Permanent Residence",
                "fields": [
                    {
                        "field_id": "form1[0].#subform[0].TextField1[0]",
                        "field_type": "Tx",
                        "label": "Family Name",
                        "required": True,
                        "properties": {"maxLength": 50},
                        "page_number": 1,
                        "tooltip": "Enter your family name as it appears on your birth certificate"
                    }
                ],
                "total_fields": 739,
                "metadata": {
                    "source": "USCIS",
                    "expiration_date": "10/15/2025"
                }
            }
        } 