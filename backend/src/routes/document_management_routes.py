from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, status
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

from ..services.document_tracking_service import DocumentTrackingService
from ..models.document import DocumentStatus, DocumentMetadata, DocumentResponse

router = APIRouter(
    prefix="/api/v1/clients/{client_id}/documents",
    tags=["documents"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Not authenticated"
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not authorized to perform this action"
        }
    }
)
document_service = DocumentTrackingService()

class DocumentStatusUpdate(BaseModel):
    """
    Schema for document status updates.
    
    Attributes:
        status: New status for the document
        reason: Optional reason for the status change
    """
    status: DocumentStatus
    reason: Optional[str] = None

@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload New Document",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Document uploaded successfully",
            "model": DocumentResponse
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid input or file upload failed"
        }
    }
)
async def upload_document(
    client_id: str,
    file: UploadFile = File(..., description="The document file to upload (PDF, image, etc.)"),
    document_type: str = Form(..., description="Type of document (e.g., passport, birth_certificate)"),
    description: Optional[str] = Form(None, description="Optional description of the document"),
    metadata: Optional[dict] = Form(None, description="Additional metadata as key-value pairs")
):
    """
    Upload a new document for a client.
    
    The document will be stored securely and associated with the specified client.
    Initial status will be set to PENDING.
    
    Args:
        client_id: Client's unique identifier
        file: The document file to upload (PDF, image, etc.)
        document_type: Type of document (e.g., "passport", "birth_certificate")
        description: Optional description of the document
        metadata: Optional additional metadata as key-value pairs
    
    Returns:
        DocumentResponse: Uploaded document details including generated ID
        
    Raises:
        HTTPException: If file upload fails or input is invalid
    """
    try:
        contents = await file.read()
        document = await document_service.upload_document(
            client_id=client_id,
            file_name=file.filename,
            content_type=file.content_type,
            file_content=contents,
            document_type=document_type,
            description=description,
            metadata=metadata
        )
        return document
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        await file.close()

@router.put(
    "/{document_id}/status",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Document Status",
    responses={
        status.HTTP_200_OK: {
            "description": "Document status updated successfully",
            "model": DocumentResponse
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid status update request"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Document not found"
        }
    }
)
async def update_document_status(
    client_id: str,
    document_id: str,
    status_update: DocumentStatusUpdate
):
    """
    Update the status of a document (approve/reject/archive).
    
    This endpoint allows changing the document's status and optionally providing a reason
    for the status change.
    
    Args:
        client_id: Client's unique identifier
        document_id: Document's unique identifier
        status_update: New status and optional reason
        
    Returns:
        DocumentResponse: Updated document details
        
    Raises:
        HTTPException: If document not found or status update is invalid
    """
    try:
        document = await document_service.update_document_status(
            client_id=client_id,
            document_id=document_id,
            status=status_update.status,
            reason=status_update.reason
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "",
    response_model=List[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Client Documents",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved documents",
            "model": List[DocumentResponse]
        }
    }
)
async def get_documents(
    client_id: str,
    status: Optional[DocumentStatus] = Query(
        None,
        description="Filter by document status (pending/approved/rejected/archived)"
    ),
    document_type: Optional[str] = Query(
        None,
        description="Filter by document type (e.g., passport, birth_certificate)"
    )
):
    """
    List all documents for a client with optional filters.
    
    Retrieve a list of all documents associated with the specified client.
    Results can be filtered by status and/or document type.
    
    Args:
        client_id: Client's unique identifier
        status: Optional status filter (pending/approved/rejected/archived)
        document_type: Optional document type filter
    
    Returns:
        List[DocumentResponse]: List of documents matching the criteria
        
    Note:
        Returns an empty list if no documents match the criteria
    """
    try:
        documents = await document_service.get_client_documents(
            client_id=client_id,
            status=status,
            document_type=document_type
        )
        return documents
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document Details",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved document details",
            "model": DocumentResponse
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Document not found"
        }
    }
)
async def get_document(
    client_id: str,
    document_id: str
):
    """
    Get details of a specific document.
    
    Retrieve detailed information about a specific document,
    including its metadata and current status.
    
    Args:
        client_id: Client's unique identifier
        document_id: Document's unique identifier
    
    Returns:
        DocumentResponse: Document details
        
    Raises:
        HTTPException: If document not found
    """
    try:
        document = await document_service.get_document(
            client_id=client_id,
            document_id=document_id
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Document",
    responses={
        status.HTTP_200_OK: {
            "description": "Document deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Document deleted successfully"}
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Document not found"
        }
    }
)
async def delete_document(
    client_id: str,
    document_id: str
):
    """
    Delete/archive a document.
    
    Permanently removes a document from the system.
    This action cannot be undone.
    
    Args:
        client_id: Client's unique identifier
        document_id: Document's unique identifier
    
    Returns:
        dict: Deletion confirmation message
        
    Raises:
        HTTPException: If document not found or deletion fails
    """
    try:
        await document_service.delete_document(
            client_id=client_id,
            document_id=document_id
        )
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) 