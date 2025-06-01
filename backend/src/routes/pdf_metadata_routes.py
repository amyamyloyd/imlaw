from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from services.pdf_storage_service import PDFStorageService
from services.pdf_metadata_service import PDFMetadataService
from services.field_mapping_service import FieldMappingService, FieldMapping
from services.version_control_service import VersionControlService, FormVersion

router = APIRouter(
    prefix="/api/pdf-metadata",
    tags=["PDF Metadata"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# Initialize services
metadata_service = PDFMetadataService()
storage_service = PDFStorageService()
mapping_service = FieldMappingService()
version_service = VersionControlService()

# Pydantic models for request/response
class FieldDefinition(BaseModel):
    field_id: str
    field_type: str
    field_name: str
    field_value: Optional[str] = None
    position: dict
    properties: dict

class FormMetadata(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    pages: int
    created_at: datetime
    updated_at: datetime
    fields: List[FieldDefinition]

# Example responses for documentation
EXAMPLE_FIELD_MAPPING = {
    "form_type": "i485",
    "form_version": "2024",
    "field_id": "Pt1Line1a_FamilyName",
    "canonical_name": "applicant.lastName",
    "description": "Applicant's family name (last name)",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "metadata": {
        "section": "Part 1. Information About You",
        "subsection": "Your Full Name"
    }
}

EXAMPLE_FORM_VERSION = {
    "form_type": "i485",
    "version": "2024",
    "effective_date": "2024-01-01T00:00:00Z",
    "expiration_date": "2024-12-31T23:59:59Z",
    "changes": [
        {
            "field_id": "Pt1Line1a_FamilyName",
            "type": "modified",
            "description": "Updated field label"
        }
    ],
    "metadata": {
        "revision": "1.0",
        "release_notes": "Initial 2024 version"
    },
    "is_active": True
}

# Routes
@router.post("/forms/upload", response_model=FormMetadata)
async def upload_form(
    file: UploadFile = File(...),
    form_type: str = Query(..., description="Type of form being uploaded (e.g., i485, i130)")
):
    """
    Upload a PDF form and extract its metadata and field definitions.
    The extracted data will be stored in MongoDB.
    """
    try:
        # Save the uploaded file
        pdf_path = await storage_service.save_uploaded_file(file)
        
        # Extract metadata and field definitions
        metadata = await metadata_service.extract_metadata(pdf_path, form_type)
        
        return metadata
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/forms", response_model=List[FormMetadata])
async def list_forms(
    form_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    List all available form metadata, optionally filtered by form type.
    Supports pagination.
    """
    try:
        forms = await metadata_service.list_forms(form_type, page, limit)
        return forms
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forms/{form_id}", response_model=FormMetadata)
async def get_form_metadata(form_id: str):
    """
    Get metadata and field definitions for a specific form.
    """
    try:
        form = await metadata_service.get_form_metadata(form_id)
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        return form
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forms/{form_id}/fields", response_model=List[FieldDefinition])
async def get_form_fields(
    form_id: str,
    field_type: Optional[str] = None
):
    """
    Get field definitions for a specific form.
    Optionally filter by field type.
    """
    try:
        fields = await metadata_service.get_form_fields(form_id, field_type)
        if not fields:
            raise HTTPException(status_code=404, detail="Form or fields not found")
        return fields
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/forms/{form_id}")
async def delete_form_metadata(form_id: str):
    """
    Delete form metadata and field definitions from the database.
    """
    try:
        success = await metadata_service.delete_form_metadata(form_id)
        if not success:
            raise HTTPException(status_code=404, detail="Form not found")
        return {"message": "Form metadata deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forms/{form_id}/fields/update", response_model=FormMetadata)
async def update_field_definitions(
    form_id: str,
    fields: List[FieldDefinition]
):
    """
    Update field definitions for a specific form.
    """
    try:
        updated_form = await metadata_service.update_field_definitions(form_id, fields)
        if not updated_form:
            raise HTTPException(status_code=404, detail="Form not found")
        return updated_form
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Field Mapping Routes
@router.post(
    "/mappings",
    response_model=str,
    summary="Create Field Mapping",
    description="Create a new mapping between a form-specific field ID and a canonical field name.",
    responses={
        201: {
            "description": "Mapping created successfully",
            "content": {
                "application/json": {
                    "example": "507f1f77bcf86cd799439011"
                }
            }
        },
        400: {
            "description": "Invalid mapping data"
        }
    }
)
async def create_field_mapping(
    mapping: FieldMapping = Body(
        ...,
        example=EXAMPLE_FIELD_MAPPING,
        description="Field mapping data"
    )
):
    """Create a new field mapping"""
    try:
        mapping_id = await mapping_service.create_mapping(mapping)
        return mapping_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/mappings/{form_type}/{version}",
    response_model=List[FieldMapping],
    summary="Get Form Mappings",
    description="Retrieve all field mappings for a specific form version.",
    responses={
        200: {
            "description": "List of field mappings",
            "content": {
                "application/json": {
                    "example": [EXAMPLE_FIELD_MAPPING]
                }
            }
        }
    }
)
async def get_form_mappings(
    form_type: str = Path(..., example="i485", description="Type of form"),
    version: str = Path(..., example="2024", description="Form version")
):
    """Get all field mappings for a form version"""
    try:
        mappings = await mapping_service.get_form_mappings(form_type, version)
        return mappings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/mappings/bulk",
    response_model=List[str],
    summary="Bulk Create Mappings",
    description="Create multiple field mappings in a single request.",
    responses={
        201: {
            "description": "Mappings created successfully",
            "content": {
                "application/json": {
                    "example": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
                }
            }
        }
    }
)
async def bulk_create_mappings(
    mappings: List[FieldMapping] = Body(
        ...,
        example=[EXAMPLE_FIELD_MAPPING],
        description="List of field mappings to create"
    )
):
    """Create multiple field mappings at once"""
    try:
        mapping_ids = await mapping_service.bulk_create_mappings(mappings)
        return mapping_ids
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/mappings/unmapped/{form_type}/{version}",
    response_model=List[str],
    summary="Get Unmapped Fields",
    description="Find fields that don't have canonical name mappings.",
    responses={
        200: {
            "description": "List of unmapped field IDs",
            "content": {
                "application/json": {
                    "example": ["Pt1Line1b_GivenName", "Pt1Line1c_MiddleName"]
                }
            }
        }
    }
)
async def get_unmapped_fields(
    form_type: str = Path(..., example="i485", description="Type of form"),
    version: str = Path(..., example="2024", description="Form version"),
    field_ids: List[str] = Query(
        ...,
        example=["Pt1Line1a_FamilyName", "Pt1Line1b_GivenName"],
        description="List of field IDs to check"
    )
):
    """Find fields that don't have mappings"""
    try:
        unmapped = await mapping_service.find_unmapped_fields(form_type, version, field_ids)
        return unmapped
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Version Control Routes
@router.post(
    "/versions",
    response_model=str,
    summary="Create Form Version",
    description="Create a new version for a form type.",
    responses={
        201: {
            "description": "Version created successfully",
            "content": {
                "application/json": {
                    "example": "507f1f77bcf86cd799439011"
                }
            }
        }
    }
)
async def create_form_version(
    version: FormVersion = Body(
        ...,
        example=EXAMPLE_FORM_VERSION,
        description="Form version data"
    )
):
    """Create a new form version"""
    try:
        version_id = await version_service.create_version(version)
        return version_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/versions/{form_type}",
    response_model=List[FormVersion],
    summary="List Form Versions",
    description="List all versions for a form type, optionally including inactive versions.",
    responses={
        200: {
            "description": "List of form versions",
            "content": {
                "application/json": {
                    "example": [EXAMPLE_FORM_VERSION]
                }
            }
        }
    }
)
async def list_form_versions(
    form_type: str = Path(..., example="i485", description="Type of form"),
    include_inactive: bool = Query(
        False,
        description="Whether to include inactive versions in the response"
    )
):
    """List all versions for a form type"""
    try:
        versions = await version_service.list_versions(form_type, include_inactive)
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/versions/{form_type}/active",
    response_model=FormVersion,
    summary="Get Active Version",
    description="Get the currently active version for a form type.",
    responses={
        200: {
            "description": "Active form version",
            "content": {
                "application/json": {
                    "example": EXAMPLE_FORM_VERSION
                }
            }
        },
        404: {
            "description": "No active version found"
        }
    }
)
async def get_active_version(
    form_type: str = Path(..., example="i485", description="Type of form")
):
    """Get the currently active version for a form type"""
    try:
        version = await version_service.get_active_version(form_type)
        if not version:
            raise HTTPException(status_code=404, detail="No active version found")
        return version
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/versions/{form_type}/{version}/activate",
    summary="Activate Form Version",
    description="Activate a specific version and deactivate all others.",
    responses={
        200: {
            "description": "Version activated successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Version activated successfully"}
                }
            }
        },
        404: {
            "description": "Version not found"
        }
    }
)
async def activate_form_version(
    form_type: str = Path(..., example="i485", description="Type of form"),
    version: str = Path(..., example="2024", description="Version to activate")
):
    """Activate a specific version and deactivate others"""
    try:
        success = await version_service.activate_version(form_type, version)
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        return {"message": "Version activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/versions/{form_type}/compare",
    response_model=Dict[str, Any],
    summary="Compare Form Versions",
    description="Compare two versions of a form and get their differences.",
    responses={
        200: {
            "description": "Version comparison results",
            "content": {
                "application/json": {
                    "example": {
                        "metadata_changes": {
                            "revision": {
                                "type": "modified",
                                "old_value": "1.0",
                                "new_value": "1.1"
                            }
                        },
                        "field_changes": ["Pt1Line1a_FamilyName"],
                        "version1_date": "2024-01-01T00:00:00Z",
                        "version2_date": "2024-06-01T00:00:00Z",
                        "newer_version": "2024"
                    }
                }
            }
        },
        404: {
            "description": "One or both versions not found"
        }
    }
)
async def compare_form_versions(
    form_type: str = Path(..., example="i485", description="Type of form"),
    version1: str = Query(..., example="2023", description="First version to compare"),
    version2: str = Query(..., example="2024", description="Second version to compare")
):
    """Compare two versions and return differences"""
    try:
        differences = await version_service.compare_versions(form_type, version1, version2)
        return differences
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 