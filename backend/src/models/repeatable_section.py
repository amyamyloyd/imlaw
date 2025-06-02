from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, field_validator

from src.models.repeatable_field import RepeatableFieldMapping

class RepeatableSection(BaseModel):
    """Definition of a repeatable section in a form"""
    section_id: str = Field(..., description="Unique identifier for the section")
    section_name: str = Field(..., description="Display name of the section")
    description: Optional[str] = Field(None, description="Description of what this section represents")
    base_page_number: int = Field(..., description="Main page number where this section starts")
    field_mappings: Dict[str, RepeatableFieldMapping] = Field(..., description="Mapping of data fields to PDF fields")
    max_entries_per_page: int = Field(..., description="Maximum entries that fit on a single page")
    supplemental_page_template: Optional[str] = Field(None, description="Template to use for supplemental pages")
    entry_prefix: Optional[str] = Field(None, description="Prefix for field IDs in this section")
    
    @field_validator("section_id")
    @classmethod
    def validate_section_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("section_id cannot be empty")
        if " " in v:
            raise ValueError("section_id cannot contain spaces")
        return v

    @field_validator("section_name")
    @classmethod
    def validate_section_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("section_name cannot be empty")
        return v

    @field_validator("base_page_number")
    @classmethod
    def validate_page_number(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("base_page_number must be positive")
        return v

    @field_validator("max_entries_per_page")
    @classmethod
    def validate_max_entries(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_entries_per_page must be positive")
        return v

    @field_validator("supplemental_page_template")
    @classmethod
    def validate_template(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("supplemental_page_template cannot be empty if provided")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "section_id": "employment_history",
                "section_name": "Employment History",
                "description": "List of previous employers",
                "base_page_number": 3,
                "field_mappings": {
                    "employer_name": {
                        "field_name": "employer_name",
                        "pdf_field_pattern": "Pt3Line{index}a_EmployerName[0]",
                        "field_type": "text",
                        "max_entries": 3
                    },
                    "start_date": {
                        "field_name": "start_date",
                        "pdf_field_pattern": "Pt3Line{index}b_StartDate[0]",
                        "field_type": "date",
                        "max_entries": 3
                    }
                },
                "max_entries_per_page": 3,
                "supplemental_page_template": "i485_supplement_employment",
                "entry_prefix": "Pt3Line"
            }
        } 