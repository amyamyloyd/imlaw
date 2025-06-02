"""PDF metadata routes"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body, Path, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from src.services.pdf_storage_service import PDFStorageService
from src.services.pdf_metadata_service import PDFMetadataService
from src.services.field_mapping_service import FieldMappingService, FieldMapping
from src.services.version_control_service import VersionControlService, FormVersion
from src.models.form_schema import FormSchema, FormFieldDefinition
import logging

router = APIRouter(
    prefix="/api/pdf-metadata",
    tags=["PDF Metadata"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# Service dependencies
def get_metadata_service():
    return PDFMetadataService()

def get_storage_service():
    return PDFStorageService()

def get_mapping_service():
    return FieldMappingService()

def get_version_service():
    return VersionControlService()

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
    form_type: str = Query(..., description="Type of form being uploaded (e.g., i485, i130)"),
    metadata_service: PDFMetadataService = Depends(get_metadata_service),
    storage_service: PDFStorageService = Depends(get_storage_service)
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
    limit: int = Query(10, ge=1, le=100),
    metadata_service: PDFMetadataService = Depends(get_metadata_service)
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
async def get_form_metadata(
    form_id: str,
    metadata_service: PDFMetadataService = Depends(get_metadata_service)
):
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
    field_type: Optional[str] = None,
    metadata_service: PDFMetadataService = Depends(get_metadata_service)
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
async def delete_form_metadata(
    form_id: str,
    metadata_service: PDFMetadataService = Depends(get_metadata_service)
):
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
    fields: List[FieldDefinition],
    metadata_service: PDFMetadataService = Depends(get_metadata_service)
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
    description="Create a new mapping between a form-specific field ID and a canonical field name."
)
async def create_field_mapping(
    mapping: FieldMapping = Body(
        ...,
        example=EXAMPLE_FIELD_MAPPING,
        description="Field mapping data"
    ),
    mapping_service: FieldMappingService = Depends(get_mapping_service)
):
    try:
        mapping_id = await mapping_service.create_mapping(mapping)
        return mapping_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/mappings/{form_type}/{version}",
    response_model=List[FieldMapping],
    summary="Get Form Mappings",
    description="Retrieve all field mappings for a specific form version."
)
async def get_form_mappings(
    form_type: str = Path(..., example="i485", description="Type of form"),
    version: str = Path(..., example="2024", description="Form version"),
    mapping_service: FieldMappingService = Depends(get_mapping_service)
):
    try:
        mappings = await mapping_service.get_form_mappings(form_type, version)
        return mappings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/mappings/bulk",
    response_model=List[str],
    summary="Bulk Create Mappings",
    description="Create multiple field mappings in a single request."
)
async def bulk_create_mappings(
    mappings: List[FieldMapping] = Body(
        ...,
        example=[EXAMPLE_FIELD_MAPPING],
        description="List of field mappings to create"
    ),
    mapping_service: FieldMappingService = Depends(get_mapping_service)
):
    try:
        mapping_ids = await mapping_service.create_mappings(mappings)
        return mapping_ids
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/mappings/unmapped/{form_type}/{version}",
    response_model=List[str],
    summary="Get Unmapped Fields",
    description="Find fields that don't have canonical name mappings."
)
async def get_unmapped_fields(
    form_type: str = Path(..., example="i485", description="Type of form"),
    version: str = Path(..., example="2024", description="Form version"),
    field_ids: List[str] = Query(
        ...,
        example=["Pt1Line1a_FamilyName", "Pt1Line1b_GivenName"],
        description="List of field IDs to check"
    ),
    mapping_service: FieldMappingService = Depends(get_mapping_service)
):
    try:
        unmapped = await mapping_service.get_unmapped_fields(form_type, version, field_ids)
        return unmapped
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/versions",
    response_model=str,
    summary="Create Form Version",
    description="Create a new version for a form type."
)
async def create_form_version(
    version: FormVersion = Body(
        ...,
        example=EXAMPLE_FORM_VERSION,
        description="Form version data"
    ),
    version_service: VersionControlService = Depends(get_version_service)
):
    try:
        version_id = await version_service.create_version(version)
        return version_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/versions/{form_type}",
    response_model=List[FormVersion],
    summary="List Form Versions",
    description="List all versions for a form type, optionally including inactive versions."
)
async def list_form_versions(
    form_type: str = Path(..., example="i485", description="Type of form"),
    include_inactive: bool = Query(
        False,
        description="Whether to include inactive versions in the response"
    ),
    version_service: VersionControlService = Depends(get_version_service)
):
    try:
        versions = await version_service.list_versions(form_type, include_inactive)
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/versions/{form_type}/active",
    response_model=FormVersion,
    summary="Get Active Version",
    description="Get the currently active version for a form type."
)
async def get_active_version(
    form_type: str = Path(..., example="i485", description="Type of form"),
    version_service: VersionControlService = Depends(get_version_service)
):
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
    description="Activate a specific version and deactivate all others."
)
async def activate_form_version(
    form_type: str = Path(..., example="i485", description="Type of form"),
    version: str = Path(..., example="2024", description="Version to activate"),
    version_service: VersionControlService = Depends(get_version_service)
):
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
    description="Compare two versions of a form and get their differences."
)
async def compare_form_versions(
    form_type: str = Path(..., example="i485", description="Type of form"),
    version1: str = Query(..., example="2023", description="First version to compare"),
    version2: str = Query(..., example="2024", description="Second version to compare"),
    version_service: VersionControlService = Depends(get_version_service)
):
    try:
        differences = await version_service.compare_versions(form_type, version1, version2)
        if not differences:
            raise HTTPException(status_code=404, detail="One or both versions not found")
        return differences
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 