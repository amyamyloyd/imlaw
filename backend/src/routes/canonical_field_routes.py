from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.canonical_field import (
    CanonicalField,
    FormFieldMapping,
    ValidationRule,
    DataType
)
from services.canonical_field_service import CanonicalFieldService
from auth.dependencies import get_current_user, User
from config.database import Database

router = APIRouter(
    prefix="/api/canonical-fields",
    tags=["Canonical Fields"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

async def get_field_service() -> CanonicalFieldService:
    """Get canonical field service instance"""
    db = Database.get_db()
    return CanonicalFieldService(db)

# Example data for API docs
EXAMPLE_CANONICAL_FIELD = {
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
        }
    ],
    "category": "personal",
    "required": True,
    "group_name": "name",
    "aliases": ["surname", "last_name"]
}

EXAMPLE_FORM_MAPPING = {
    "form_type": "I-485",
    "form_version": "2024",
    "field_id": "Pt1Line1a_FamilyName",
    "mapping_type": "direct"
}

@router.post(
    "",
    response_model=str,
    status_code=201,
    summary="Create Canonical Field",
    description="Create a new canonical field definition.",
    responses={
        201: {
            "description": "Field created successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "value": "507f1f77bcf86cd799439011"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid field data or duplicate field name"
        }
    }
)
async def create_canonical_field(
    field: CanonicalField = Body(..., examples={"example": {"value": EXAMPLE_CANONICAL_FIELD}}),
    current_user: User = Depends(get_current_user),
    field_service: CanonicalFieldService = Depends(get_field_service)
):
    """Create a new canonical field"""
    try:
        field_id = await field_service.create_field(field)
        return field_id
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{field_name}",
    response_model=CanonicalField,
    summary="Get Canonical Field",
    description="Get a canonical field by its name.",
    responses={
        404: {
            "description": "Field not found"
        }
    }
)
async def get_canonical_field(
    field_name: str = Path(..., examples={"example": {"value": "family_name"}}),
    field_service: CanonicalFieldService = Depends(get_field_service)
):
    """Get a canonical field by name"""
    field = await field_service.get_field(field_name)
    if not field:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found"
        )
    return field

@router.get(
    "",
    response_model=List[CanonicalField],
    summary="List Canonical Fields",
    description="Get a list of canonical fields with optional filtering."
)
async def list_canonical_fields(
    category: Optional[str] = Query(None, example="personal"),
    group_name: Optional[str] = Query(None, example="name"),
    data_type: Optional[DataType] = Query(None, example=DataType.STRING),
    include_inactive: bool = Query(False, description="Include inactive fields"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
):
    """List canonical fields with filtering"""
    field_service = await get_field_service()
    fields = await field_service.get_fields(
        category=category,
        group_name=group_name,
        data_type=data_type,
        include_inactive=include_inactive,
        page=page,
        page_size=page_size
    )
    return fields

@router.get(
    "/search/{search_text}",
    response_model=List[CanonicalField],
    summary="Search Canonical Fields",
    description="Search for canonical fields by name, aliases, or display name."
)
async def search_canonical_fields(
    search_text: str = Path(..., example="name"),
    exact_match: bool = Query(False, description="Require exact match")
):
    """Search for canonical fields"""
    field_service = await get_field_service()
    fields = await field_service.search_fields(
        search_text=search_text,
        exact_match=exact_match
    )
    return fields

@router.patch(
    "/{field_name}",
    response_model=bool,
    summary="Update Canonical Field",
    description="Update a canonical field's properties.",
    responses={
        404: {
            "description": "Field not found"
        }
    }
)
async def update_canonical_field(
    field_name: str = Path(..., example="family_name"),
    updates: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Update a canonical field"""
    field_service = await get_field_service()
    # First check if field exists
    field = await field_service.get_field(field_name)
    if not field:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found"
        )
    
    try:
        success = await field_service.update_field(
            field_name=field_name,
            updates=updates,
            changed_by=current_user.username
        )
        return success
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/{field_name}",
    response_model=bool,
    summary="Delete Canonical Field",
    description="Delete a canonical field if it has no active mappings.",
    responses={
        404: {
            "description": "Field not found"
        },
        400: {
            "description": "Field has active mappings"
        }
    }
)
async def delete_canonical_field(
    field_name: str = Path(..., example="family_name"),
    current_user: User = Depends(get_current_user)
):
    """Delete a canonical field"""
    field_service = await get_field_service()
    # First check if field exists
    field = await field_service.get_field(field_name)
    if not field:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found"
        )
    
    try:
        success = await field_service.delete_field(field_name)
        return success
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/{field_name}/mappings",
    response_model=bool,
    summary="Add Form Mapping",
    description="Add a form field mapping to a canonical field.",
    responses={
        404: {
            "description": "Field not found"
        }
    }
)
async def add_form_mapping(
    field_name: str = Path(..., example="family_name"),
    mapping: FormFieldMapping = Body(..., example=EXAMPLE_FORM_MAPPING),
    current_user: User = Depends(get_current_user)
):
    """Add a form field mapping"""
    field_service = await get_field_service()
    # First check if field exists
    field = await field_service.get_field(field_name)
    if not field:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found"
        )
    
    try:
        success = await field_service.add_form_mapping(field_name, mapping)
        return success
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/{field_name}/mappings/{form_type}/{form_version}/{field_id}",
    response_model=bool,
    summary="Remove Form Mapping",
    description="Remove a form field mapping from a canonical field.",
    responses={
        404: {
            "description": "Field or mapping not found"
        }
    }
)
async def remove_form_mapping(
    field_name: str = Path(..., example="family_name"),
    form_type: str = Path(..., example="I-485"),
    form_version: str = Path(..., example="2024"),
    field_id: str = Path(..., example="Pt1Line1a_FamilyName"),
    current_user: User = Depends(get_current_user)
):
    """Remove a form field mapping"""
    field_service = await get_field_service()
    # First check if field exists
    field = await field_service.get_field(field_name)
    if not field:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found"
        )
    
    try:
        success = await field_service.remove_form_mapping(
            field_name=field_name,
            form_type=form_type,
            form_version=form_version,
            field_id=field_id
        )
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping not found for field '{field_name}'"
            )
        return success
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/form/{form_type}/{form_version}",
    response_model=List[CanonicalField],
    summary="Get Fields by Form",
    description="Get all canonical fields mapped to a specific form version."
)
async def get_fields_by_form(
    form_type: str = Path(..., example="I-485"),
    form_version: str = Path(..., example="2024")
):
    """Get fields mapped to a form"""
    field_service = await get_field_service()
    fields = await field_service.get_fields_by_form(form_type, form_version)
    return fields

@router.post(
    "/{field_name}/usage",
    response_model=bool,
    summary="Record Field Usage",
    description="Record usage of a canonical field, optionally with form type."
)
async def record_field_usage(
    field_name: str = Path(..., example="family_name"),
    form_type: Optional[str] = Query(None, example="I-485")
):
    """Record field usage"""
    field_service = await get_field_service()
    # First check if field exists
    field = await field_service.get_field(field_name)
    if not field:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found"
        )
    
    success = await field_service.record_usage(field_name, form_type)
    return success

@router.post(
    "/{field_name}/errors",
    response_model=bool,
    summary="Record Validation Error",
    description="Increment the error count for a canonical field."
)
async def record_validation_error(
    field_name: str = Path(..., example="family_name")
):
    """Record validation error"""
    field_service = await get_field_service()
    # First check if field exists
    field = await field_service.get_field(field_name)
    if not field:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found"
        )
    
    success = await field_service.increment_error_count(field_name)
    return success 