"""Client Profile Data Model.

This module defines the data model for client profiles, including:
- Core personal information
- Contact details
- Document tracking
- Support for repeatable sections
- Partial save functionality

The model uses Pydantic for validation and MongoDB-compatible field types.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, constr, field_validator
from bson import ObjectId

class RepeatableSection(BaseModel):
    """Base model for repeatable sections within a client profile."""
    section_type: str = Field(..., description="Type of repeatable section (e.g., 'address', 'employment')")
    order: int = Field(0, description="Order of this section within its type")
    is_complete: bool = Field(False, description="Whether this section is complete")
    data: Dict[str, Any] = Field(default_factory=dict, description="Section-specific data")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Address(RepeatableSection):
    """Address information with validation."""
    section_type: str = "address"
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "street": "",
            "unit": "",
            "city": "",
            "state": "",
            "zip": "",
            "country": "USA",
            "type": "home",  # home, work, mailing
            "years_at_address": 0,
            "is_current": True
        }
    )

class Employment(RepeatableSection):
    """Employment history information."""
    section_type: str = "employment"
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "employer": "",
            "title": "",
            "start_date": None,
            "end_date": None,
            "is_current": False,
            "address": {},
            "supervisor": "",
            "contact_number": "",
            "reason_for_leaving": ""
        }
    )

class Education(RepeatableSection):
    """Educational history information."""
    section_type: str = "education"
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "institution": "",
            "degree": "",
            "field_of_study": "",
            "start_date": None,
            "end_date": None,
            "is_completed": False,
            "address": {}
        }
    )

class FamilyMember(RepeatableSection):
    """Family member information."""
    section_type: str = "family"
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "relationship": "",
            "name": "",
            "date_of_birth": None,
            "citizenship": "",
            "residence_status": "",
            "address": {},
            "is_dependent": False
        }
    )

class SaveProgress(BaseModel):
    """Tracks progress of partial saves."""
    last_section: str = Field("", description="Last section being edited")
    last_field: str = Field("", description="Last field being edited")
    completion_percentage: float = Field(0, description="Overall completion percentage")
    completed_sections: List[str] = Field(default_factory=list, description="List of completed sections")
    last_saved: datetime = Field(default_factory=datetime.utcnow)
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)

class ClientProfile(BaseModel):
    """Client profile data model."""
    
    client_id: str = Field(..., description="Unique identifier for the client")
    email: EmailStr = Field(..., description="Primary email address")
    first_name: str = Field(..., description="Client's first name")
    last_name: str = Field(..., description="Client's last name")
    phone: str = Field(..., description="Primary phone number")
    
    @field_validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        import re
        if not re.match(r'^\+?1?\d{9,15}$', v):
            raise ValueError('Invalid phone number format')
        return v
    
    def update_completion_status(self) -> None:
        """Update completion status and percentage."""
        completed = len(self.save_progress.completed_sections)
        total_sections = 4  # Basic, Employment, Education, Family
        
        self.save_progress.completion_percentage = (completed / total_sections) * 100
        self.is_complete = self.save_progress.completion_percentage == 100
        self.save_progress.last_saved = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_repeatable_section(
        self,
        section_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Add a new repeatable section of the specified type.
        
        Args:
            section_type: Type of section to add (address, employment, education, family)
            data: Section-specific data
        """
        section_map = {
            "address": (self.addresses, Address),
            "employment": (self.employment, Employment),
            "education": (self.education, Education),
            "family": (self.family_members, FamilyMember)
        }
        
        if section_type not in section_map:
            raise ValueError(f"Invalid section type: {section_type}")
            
        section_list, section_class = section_map[section_type]
        new_section = section_class(
            order=len(section_list),
            data=data
        )
        section_list.append(new_section)
        self.update_completion_status() 