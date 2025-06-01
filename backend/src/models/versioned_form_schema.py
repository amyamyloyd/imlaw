from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, constr, validator
from enum import Enum
from .form_schema import FormSchema, FormFieldDefinition, FieldType, Position, FieldFlags

class SchemaVersion(BaseModel):
    """Version information for a form schema"""
    major: int = Field(..., ge=0, description="Major version number")
    minor: int = Field(..., ge=0, description="Minor version number")
    patch: int = Field(..., ge=0, description="Patch version number")
    released: datetime = Field(default_factory=datetime.utcnow, description="Version release date")
    deprecated: bool = Field(default=False, description="Whether this version is deprecated")
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @validator("major", "minor", "patch")
    def validate_version_numbers(cls, v):
        if v < 0:
            raise ValueError("Version numbers must be non-negative")
        return v

class FieldChange(BaseModel):
    """Represents a change in a form field between versions"""
    field_id: str = Field(..., description="ID of the changed field")
    change_type: str = Field(..., description="Type of change (added, removed, modified)")
    previous_value: Optional[Dict[str, Any]] = Field(None, description="Field state before change")
    new_value: Optional[Dict[str, Any]] = Field(None, description="Field state after change")
    
    @validator("change_type")
    def validate_change_type(cls, v):
        valid_types = {"added", "removed", "modified"}
        if v not in valid_types:
            raise ValueError(f"change_type must be one of {valid_types}")
        return v

class VersionDiff(BaseModel):
    """Differences between two schema versions"""
    from_version: str = Field(..., description="Source version")
    to_version: str = Field(..., description="Target version")
    changes: List[FieldChange] = Field(default_factory=list, description="List of field changes")
    migration_notes: Optional[str] = Field(None, description="Notes about version migration")
    breaking_changes: bool = Field(default=False, description="Whether changes break backward compatibility")

class VersionedFormSchema(FormSchema):
    """Extended form schema with versioning support"""
    schema_version: SchemaVersion = Field(..., description="Schema version information")
    previous_version: Optional[str] = Field(None, description="Reference to previous schema version")
    next_version: Optional[str] = Field(None, description="Reference to next schema version")
    version_changes: Optional[VersionDiff] = Field(None, description="Changes from previous version")
    compatibility: List[str] = Field(default_factory=list, description="Compatible schema versions")
    migration_strategy: Optional[str] = Field(None, description="Strategy for migrating to this version")
    
    class Config:
        schema_extra = {
            "example": {
                "form_type": "I-485",
                "version": "10/15/2023",
                "title": "Application to Register Permanent Residence",
                "schema_version": {
                    "major": 1,
                    "minor": 0,
                    "patch": 0,
                    "released": "2024-01-01T00:00:00Z",
                    "deprecated": False
                },
                "fields": [
                    {
                        "field_id": "form1[0].#subform[0].TextField1[0]",
                        "field_type": "Tx",
                        "field_name": "Family Name",
                        "required": True,
                        "properties": {"maxLength": 50},
                        "page_number": 1,
                        "tooltip": "Enter your family name as it appears on your birth certificate"
                    }
                ],
                "total_fields": 739,
                "compatibility": ["1.0.0", "0.9.0"],
                "migration_strategy": "in-place"
            }
        }

class VersionedFormSchemaCollection:
    """MongoDB collection configuration for versioned form schemas"""
    name = "versioned_form_schemas"
    indexes = [
        {
            "keys": [("form_type", 1), ("schema_version.major", 1), 
                    ("schema_version.minor", 1), ("schema_version.patch", 1)],
            "unique": True,
            "name": "unique_version"
        },
        {
            "keys": [("form_type", 1), ("schema_version.released", -1)],
            "name": "latest_version"
        },
        {
            "keys": [("form_type", 1), ("compatibility", 1)],
            "name": "compatibility_lookup"
        }
    ]
    validation = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["form_type", "schema_version", "fields", "total_fields"],
            "properties": {
                "form_type": {"bsonType": "string"},
                "schema_version": {
                    "bsonType": "object",
                    "required": ["major", "minor", "patch", "released"],
                    "properties": {
                        "major": {"bsonType": "int"},
                        "minor": {"bsonType": "int"},
                        "patch": {"bsonType": "int"},
                        "released": {"bsonType": "date"},
                        "deprecated": {"bsonType": "bool"}
                    }
                },
                "fields": {
                    "bsonType": "array",
                    "minItems": 1
                },
                "total_fields": {"bsonType": "int", "minimum": 1},
                "compatibility": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                }
            }
        }
    } 