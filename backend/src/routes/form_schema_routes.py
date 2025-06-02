"""Form schema routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.models.form_schema import FormSchema
from src.services.form_schema_service import FormSchemaService
from src.auth.dependencies import get_current_user
from src.models.user import User

router = APIRouter(
    prefix="/api/form-schemas",
    tags=["Form Schemas"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# Service dependency
def get_schema_service():
    return FormSchemaService()

@router.post("/", response_model=str)
async def create_form_schema(
    schema: FormSchema = Body(..., description="Form schema to create"),
    current_user: User = Depends(get_current_user),
    schema_service: FormSchemaService = Depends(get_schema_service)
):
    """Create a new form schema"""
    try:
        schema_id = await schema_service.create_schema(schema)
        return schema_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{form_type}/{version}", response_model=FormSchema)
async def get_form_schema(
    form_type: str = Path(..., description="Type of form"),
    version: str = Path(..., description="Form version"),
    schema_service: FormSchemaService = Depends(get_schema_service)
):
    """Get a specific form schema"""
    try:
        schema = await schema_service.get_schema(form_type, version)
        if not schema:
            raise HTTPException(status_code=404, detail="Form schema not found")
        return schema
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{form_type}", response_model=List[FormSchema])
async def list_form_schemas(
    form_type: str = Path(..., description="Type of form"),
    include_inactive: bool = Query(False, description="Include inactive schemas"),
    schema_service: FormSchemaService = Depends(get_schema_service)
):
    """List all schemas for a form type"""
    try:
        schemas = await schema_service.list_schemas(form_type, include_inactive)
        return schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{form_type}/{version}", response_model=FormSchema)
async def update_form_schema(
    form_type: str = Path(..., description="Type of form"),
    version: str = Path(..., description="Form version"),
    schema: FormSchema = Body(..., description="Updated form schema"),
    current_user: User = Depends(get_current_user),
    schema_service: FormSchemaService = Depends(get_schema_service)
):
    """Update a form schema"""
    try:
        updated_schema = await schema_service.update_schema(form_type, version, schema)
        if not updated_schema:
            raise HTTPException(status_code=404, detail="Form schema not found")
        return updated_schema
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{form_type}/{version}")
async def delete_form_schema(
    form_type: str = Path(..., description="Type of form"),
    version: str = Path(..., description="Form version"),
    current_user: User = Depends(get_current_user),
    schema_service: FormSchemaService = Depends(get_schema_service)
):
    """Delete a form schema"""
    try:
        success = await schema_service.delete_schema(form_type, version)
        if not success:
            raise HTTPException(status_code=404, detail="Form schema not found")
        return {"message": "Form schema deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 