from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class FormEntry(BaseModel):
    """A single form entry for a client."""
    form_type: str = Field(..., description="Form identifier (e.g., 'I-485')")
    form_version: str = Field(..., description="Form version")
    status: str = Field("draft", description="Form status (draft, complete, submitted)")
    field_data: Dict[str, Any] = Field(..., description="Form field values keyed by field_id")
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional form metadata")

class ClientEntry(BaseModel):
    """Schema for storing client information and form entries."""
    client_id: str = Field(..., description="Unique identifier for the client")
    first_name: str = Field(..., description="Client's first name")
    middle_name: Optional[str] = Field(None, description="Client's middle name")
    last_name: str = Field(..., description="Client's last name")
    email: str = Field(..., description="Client's email address")
    phone: Optional[str] = Field(None, description="Client's phone number")
    date_of_birth: datetime = Field(..., description="Client's date of birth")
    forms: List[FormEntry] = Field(default_factory=list, description="List of client's form entries")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional client metadata")

    class Config:
        schema_extra = {
            "example": {
                "client_id": "C123456",
                "first_name": "John",
                "middle_name": "Robert",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "date_of_birth": "1990-01-01T00:00:00Z",
                "forms": [
                    {
                        "form_type": "I-485",
                        "form_version": "10/15/2023",
                        "status": "draft",
                        "field_data": {
                            "form1[0].#subform[0].TextField1[0]": "Doe",
                            "form1[0].#subform[0].TextField2[0]": "John"
                        },
                        "metadata": {
                            "last_saved_by": "john.doe@example.com",
                            "completion_percentage": 45
                        }
                    }
                ],
                "metadata": {
                    "preferred_language": "English",
                    "timezone": "America/New_York"
                }
            }
        } 