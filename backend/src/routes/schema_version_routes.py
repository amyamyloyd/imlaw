"""Schema Version Routes for managing form metadata versions via API.

This module provides FastAPI routes for managing form metadata versions, including:
- Version creation and retrieval
- Version activation/deactivation
- Version comparison and diff generation
- Version history and changelog management
- Admin review and approval workflow

Key Features:
- RESTful API endpoints for version management
- Version comparison and diff calculation
- Change tracking with user attribution
- Review and approval workflow
- Audit trail and history tracking

Example Usage:
    # Create new version
    POST /api/v1/versions
    {
        "form_type": "i485",
        "version": "2024",
        "effective_date": "2024-01-01T00:00:00Z"
    }
    
    # Get active version
    GET /api/v1/versions/i485/active
    
    # Compare versions
    GET /api/v1/versions/i485/compare?v1=2023&v2=2024
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.versioned_form_schema import VersionedFormSchema, SchemaVersion, VersionDiff
from services.versioned_schema_service import VersionedSchemaService
from services.schema_diff_service import SchemaDiffService
from services.schema_migration_service import SchemaMigrationService
from src.db.database import get_db
from src.services.version_control_service import VersionControlService, FormVersion
from src.models.user import User

router = APIRouter(prefix="/api/v1/versions", tags=["versions"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_version(
    version: FormVersion,
    service: VersionControlService = Depends()
) -> Dict[str, str]:
    """Create a new form metadata version.
    
    Args:
        version (FormVersion): Version metadata to create
        service (VersionControlService): Injected version control service
        
    Returns:
        Dict[str, str]: Dictionary containing the ID of created version
        
    Raises:
        HTTPException: If version creation fails
        
    Example:
        POST /api/v1/versions
        {
            "form_type": "i485",
            "version": "2024",
            "effective_date": "2024-01-01T00:00:00Z"
        }
    """
    try:
        version_id = await service.create_version(version)
        return {"id": version_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{form_type}/active")
async def get_active_version(
    form_type: str,
    service: VersionControlService = Depends()
) -> Optional[FormVersion]:
    """Get the currently active version for a form type.
    
    Args:
        form_type (str): Type of form to get active version for
        service (VersionControlService): Injected version control service
        
    Returns:
        Optional[FormVersion]: Active version if found
        
    Raises:
        HTTPException: If form type not found
        
    Example:
        GET /api/v1/versions/i485/active
    """
    version = await service.get_active_version(form_type)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active version found for form type: {form_type}"
        )
    return version

@router.get("/{form_type}")
async def list_versions(
    form_type: str,
    include_inactive: bool = False,
    service: VersionControlService = Depends()
) -> List[FormVersion]:
    """List all versions for a form type.
    
    Args:
        form_type (str): Type of form to list versions for
        include_inactive (bool): Whether to include inactive versions
        service (VersionControlService): Injected version control service
        
    Returns:
        List[FormVersion]: List of versions, sorted by effective date
        
    Example:
        GET /api/v1/versions/i485?include_inactive=true
    """
    return await service.list_versions(form_type, include_inactive)

@router.get("/{form_type}/compare")
async def compare_versions(
    form_type: str,
    v1: str,
    v2: str,
    service: VersionControlService = Depends()
) -> Optional[Dict[str, Any]]:
    """Compare two versions and get their differences.
    
    Args:
        form_type (str): Type of form to compare
        v1 (str): First version identifier
        v2 (str): Second version identifier
        service (VersionControlService): Injected version control service
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing:
            - metadata_changes: Changes in metadata fields
            - field_changes: List of changed field IDs
            - version1_date: Effective date of first version
            - version2_date: Effective date of second version
            - newer_version: Which version is newer
            
    Raises:
        HTTPException: If either version not found
        
    Example:
        GET /api/v1/versions/i485/compare?v1=2023&v2=2024
    """
    diff = await service.compare_versions(form_type, v1, v2)
    if not diff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not compare versions {v1} and {v2}"
        )
    return diff

@router.post("/{form_type}/{version}/activate")
async def activate_version(
    form_type: str,
    version: str,
    service: VersionControlService = Depends()
) -> Dict[str, bool]:
    """Activate a specific version and deactivate all others.
    
    Args:
        form_type (str): Type of form
        version (str): Version identifier to activate
        service (VersionControlService): Injected version control service
        
    Returns:
        Dict[str, bool]: Success status
        
    Raises:
        HTTPException: If version not found or activation fails
        
    Example:
        POST /api/v1/versions/i485/2024/activate
    """
    success = await service.activate_version(form_type, version)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found"
        )
    return {"success": True}

@router.post("/{form_type}/{version}/deactivate")
async def deactivate_version(
    form_type: str,
    version: str,
    service: VersionControlService = Depends()
) -> Dict[str, bool]:
    """Deactivate a specific version.
    
    Args:
        form_type (str): Type of form
        version (str): Version identifier to deactivate
        service (VersionControlService): Injected version control service
        
    Returns:
        Dict[str, bool]: Success status
        
    Example:
        POST /api/v1/versions/i485/2024/deactivate
    """
    await service.deactivate_versions(form_type)
    return {"success": True}

@router.get("/{version}", response_model=VersionedFormSchema)
async def get_version(
    form_type: str,
    version: str,
    db=Depends(get_db)
):
    """Get a specific version of a form schema"""
    schema_service = VersionedSchemaService(db)
    schema = await schema_service.get_version(form_type, version)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema version not found")
    return schema

@router.get("/{from_version}/diff/{to_version}", response_model=VersionDiff)
async def get_version_diff(
    form_type: str,
    from_version: str,
    to_version: str,
    db=Depends(get_db)
):
    """Get the differences between two schema versions"""
    schema_service = VersionedSchemaService(db)
    diff_service = SchemaDiffService()
    
    # Get both schemas
    old_schema = await schema_service.get_version(form_type, from_version)
    if not old_schema:
        raise HTTPException(status_code=404, detail=f"Schema version {from_version} not found")
        
    new_schema = await schema_service.get_version(form_type, to_version)
    if not new_schema:
        raise HTTPException(status_code=404, detail=f"Schema version {to_version} not found")
    
    # Calculate diff
    diff = diff_service.calculate_diff(old_schema, new_schema)
    return diff

@router.post("/{version}/approve")
async def approve_version(
    form_type: str,
    version: str,
    comment: Optional[str] = None,
    db=Depends(get_db)
):
    """Approve a schema version"""
    schema_service = VersionedSchemaService(db)
    try:
        await schema_service.approve_version(form_type, version, comment)
        return {"message": "Version approved successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{version}/reject")
async def reject_version(
    form_type: str,
    version: str,
    reason: str,
    db=Depends(get_db)
):
    """Reject a schema version"""
    schema_service = VersionedSchemaService(db)
    try:
        await schema_service.reject_version(form_type, version, reason)
        return {"message": "Version rejected successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{version}/revert")
async def revert_to_version(
    form_type: str,
    version: str,
    comment: Optional[str] = None,
    db=Depends(get_db)
):
    """Revert to a previous schema version"""
    schema_service = VersionedSchemaService(db)
    try:
        new_version = await schema_service.revert_to_version(form_type, version, comment)
        return {
            "message": "Reverted successfully",
            "new_version": new_version
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{version}/changelog", response_model=List[dict])
async def get_version_changelog(
    form_type: str,
    version: str,
    db=Depends(get_db)
):
    """Get the changelog for a specific version"""
    schema_service = VersionedSchemaService(db)
    try:
        changelog = await schema_service.get_changelog(form_type, version)
        return changelog
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{version}/comment")
async def add_version_comment(
    form_type: str,
    version: str,
    comment: str,
    db=Depends(get_db)
):
    """Add a comment to a schema version"""
    schema_service = VersionedSchemaService(db)
    try:
        await schema_service.add_comment(form_type, version, comment)
        return {"message": "Comment added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 