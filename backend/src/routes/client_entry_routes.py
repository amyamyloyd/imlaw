"""Client entry routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.models.client_entry import ClientEntry
from src.services.client_entry_service import ClientEntryService
from src.auth.dependencies import get_current_user
from src.models.user import User

router = APIRouter(
    prefix="/api/client-entries",
    tags=["Client Entries"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# Service dependency
def get_entry_service():
    return ClientEntryService()

@router.post("/", response_model=str)
async def create_client_entry(
    entry: ClientEntry = Body(..., description="Client entry to create"),
    current_user: User = Depends(get_current_user),
    entry_service: ClientEntryService = Depends(get_entry_service)
):
    """Create a new client entry"""
    try:
        entry_id = await entry_service.create_entry(entry)
        return entry_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{entry_id}", response_model=ClientEntry)
async def get_client_entry(
    entry_id: str = Path(..., description="Entry ID"),
    current_user: User = Depends(get_current_user),
    entry_service: ClientEntryService = Depends(get_entry_service)
):
    """Get a specific client entry"""
    try:
        entry = await entry_service.get_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Client entry not found")
        return entry
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ClientEntry])
async def list_client_entries(
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    form_type: Optional[str] = Query(None, description="Filter by form type"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    entry_service: ClientEntryService = Depends(get_entry_service)
):
    """List client entries with optional filters"""
    try:
        entries = await entry_service.list_entries(
            client_id=client_id,
            form_type=form_type,
            page=page,
            limit=limit
        )
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{entry_id}", response_model=ClientEntry)
async def update_client_entry(
    entry_id: str = Path(..., description="Entry ID"),
    entry: ClientEntry = Body(..., description="Updated client entry"),
    current_user: User = Depends(get_current_user),
    entry_service: ClientEntryService = Depends(get_entry_service)
):
    """Update a client entry"""
    try:
        updated_entry = await entry_service.update_entry(entry_id, entry)
        if not updated_entry:
            raise HTTPException(status_code=404, detail="Client entry not found")
        return updated_entry
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{entry_id}")
async def delete_client_entry(
    entry_id: str = Path(..., description="Entry ID"),
    current_user: User = Depends(get_current_user),
    entry_service: ClientEntryService = Depends(get_entry_service)
):
    """Delete a client entry"""
    try:
        success = await entry_service.delete_entry(entry_id)
        if not success:
            raise HTTPException(status_code=404, detail="Client entry not found")
        return {"message": "Client entry deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 