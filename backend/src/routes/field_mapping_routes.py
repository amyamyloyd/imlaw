"""Field mapping routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.services.field_mapping_suggestion_service import FieldMappingSuggestionService
from src.models.field_mapping import FieldMapping, FieldMappingSuggestion
from src.models.canonical_field import CanonicalField, FormFieldMapping
from src.auth.dependencies import get_current_user
from src.db.database import Database, get_db
from src.services.field_transform_service import FieldTransformService
from src.services.canonical_field_service import CanonicalFieldService
from src.models.user import User
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/api/field-mappings",
    tags=["Field Mappings"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# Service dependencies
def get_suggestion_service():
    return FieldMappingSuggestionService()

def get_transform_service():
    return FieldTransformService()

def get_canonical_service():
    return CanonicalFieldService()

class SuggestMappingsRequest(BaseModel):
    """Request model for suggesting field mappings"""
    form_fields: List[Dict[str, Any]] = Field(
        ...,
        description="List of form fields to map"
    )
    form_type: str = Field(
        ...,
        description="Type of form (e.g., 'i-485')"
    )
    form_version: str = Field(
        ...,
        description="Version of the form"
    )
    min_confidence: Optional[float] = Field(
        default=0.7,
        description="Minimum confidence score for suggestions"
    )

class TransformValueRequest(BaseModel):
    """Request model for transforming field values"""
    value: Any = Field(
        ...,
        description="Value to transform"
    )
    transform_rule: Dict[str, Any] = Field(
        ...,
        description="Transform rule to apply"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for transformation"
    )

@router.post("/suggest")
async def suggest_mappings(
    request: SuggestMappingsRequest,
    current_user: User = Depends(get_current_user),
    suggestion_service: FieldMappingSuggestionService = Depends(get_suggestion_service)
) -> List[Dict[str, Any]]:
    """Suggest canonical field mappings for form fields"""
    try:
        suggestions = await suggestion_service.suggest_mappings(
            form_fields=request.form_fields,
            form_type=request.form_type,
            form_version=request.form_version,
            min_confidence=request.min_confidence
        )
        return suggestions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error suggesting mappings: {str(e)}"
        )

@router.post("/transform")
async def transform_value(
    request: TransformValueRequest,
    current_user: User = Depends(get_current_user),
    transform_service: FieldTransformService = Depends(get_transform_service)
) -> Dict[str, Any]:
    """Transform a field value using a transform rule"""
    try:
        transformed_value = transform_service.transform_value(
            value=request.value,
            rule=request.transform_rule,
            context=request.context
        )
        return {
            "original_value": request.value,
            "transformed_value": transformed_value
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transform request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error transforming value: {str(e)}"
        )

@router.post("/batch-transform")
async def batch_transform_values(
    request: List[TransformValueRequest],
    current_user: User = Depends(get_current_user),
    transform_service: FieldTransformService = Depends(get_transform_service)
) -> List[Dict[str, Any]]:
    """Transform multiple field values using transform rules"""
    try:
        results = []
        for item in request:
            transformed_value = transform_service.transform_value(
                value=item.value,
                rule=item.transform_rule,
                context=item.context
            )
            results.append({
                "original_value": item.value,
                "transformed_value": transformed_value
            })
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transform request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error transforming values: {str(e)}"
        ) 