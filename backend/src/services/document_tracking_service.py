"""Document Tracking Service.

This service handles document tracking for client profiles, including:
- Document upload and storage
- Document status management (pending, approved, rejected, archived)
- Document metadata management
- Document retrieval and filtering
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from fastapi import UploadFile, HTTPException
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from src.db.database import Database
from src.models.document import DocumentStatus, DocumentMetadata, DocumentResponse

class DocumentTrackingService:
    """Service for managing document tracking in client profiles."""
    
    def __init__(self):
        """Initialize service with MongoDB connection."""
        database = Database()
        self.db = database.db
        self.fs = AsyncIOMotorGridFSBucket(self.db)
        self.documents_collection = self.db['documents']
    
    async def upload_document(
        self,
        client_id: str,
        file_name: str,
        content_type: str,
        file_content: bytes,
        document_type: str,
        description: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> DocumentResponse:
        """Upload a new document and store its metadata.
        
        Args:
            client_id: Client's unique identifier
            file_name: Original file name
            content_type: File MIME type
            file_content: Binary file content
            document_type: Type of document (e.g., 'passport')
            description: Optional document description
            metadata: Optional additional metadata
            
        Returns:
            DocumentResponse: Created document details
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Upload file to GridFS
            file_metadata = {
                "client_id": client_id,
                "content_type": content_type,
                "document_type": document_type
            }
            file_id = await self.fs.upload_from_stream(
                file_name,
                file_content,
                metadata=file_metadata
            )
            
            # Create document metadata
            doc_metadata = DocumentMetadata(
                document_type=document_type,
                description=description,
                content_type=content_type,
                file_size=len(file_content),
                original_filename=file_name,
                custom_metadata=metadata
            )
            
            # Create document record
            document = {
                "client_id": client_id,
                "file_id": file_id,
                "status": DocumentStatus.PENDING,
                "metadata": doc_metadata.dict(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.documents_collection.insert_one(document)
            
            return DocumentResponse(
                id=str(result.inserted_id),
                client_id=client_id,
                status=DocumentStatus.PENDING,
                metadata=doc_metadata
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Document upload failed: {str(e)}")
    
    async def update_document_status(
        self,
        client_id: str,
        document_id: str,
        status: DocumentStatus,
        reason: Optional[str] = None
    ) -> DocumentResponse:
        """Update document status.
        
        Args:
            client_id: Client's unique identifier
            document_id: Document's unique identifier
            status: New document status
            reason: Optional reason for status change
            
        Returns:
            DocumentResponse: Updated document details
            
        Raises:
            HTTPException: If document not found or update fails
        """
        try:
            # Find and update document
            result = await self.documents_collection.find_one_and_update(
                {
                    "_id": ObjectId(document_id),
                    "client_id": client_id
                },
                {
                    "$set": {
                        "status": status,
                        "status_reason": reason,
                        "updated_at": datetime.utcnow()
                    }
                },
                return_document=True
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return DocumentResponse(
                id=str(result["_id"]),
                client_id=result["client_id"],
                status=result["status"],
                metadata=DocumentMetadata(**result["metadata"]),
                status_reason=result.get("status_reason")
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Status update failed: {str(e)}")
    
    async def get_client_documents(
        self,
        client_id: str,
        status: Optional[DocumentStatus] = None,
        document_type: Optional[str] = None
    ) -> List[DocumentResponse]:
        """Get all documents for a client with optional filters.
        
        Args:
            client_id: Client's unique identifier
            status: Optional status filter
            document_type: Optional document type filter
            
        Returns:
            List[DocumentResponse]: List of matching documents
            
        Raises:
            HTTPException: If query fails
        """
        try:
            # Build query
            query = {"client_id": client_id}
            if status:
                query["status"] = status
            if document_type:
                query["metadata.document_type"] = document_type
            
            # Get documents
            cursor = self.documents_collection.find(query)
            documents = []
            
            async for doc in cursor:
                documents.append(DocumentResponse(
                    id=str(doc["_id"]),
                    client_id=doc["client_id"],
                    status=doc["status"],
                    metadata=DocumentMetadata(**doc["metadata"]),
                    status_reason=doc.get("status_reason")
                ))
            
            return documents
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Document retrieval failed: {str(e)}")
    
    async def get_document(
        self,
        client_id: str,
        document_id: str
    ) -> Optional[DocumentResponse]:
        """Get a specific document's details.
        
        Args:
            client_id: Client's unique identifier
            document_id: Document's unique identifier
            
        Returns:
            Optional[DocumentResponse]: Document details if found
            
        Raises:
            HTTPException: If query fails
        """
        try:
            doc = await self.documents_collection.find_one({
                "_id": ObjectId(document_id),
                "client_id": client_id
            })
            
            if not doc:
                return None
            
            return DocumentResponse(
                id=str(doc["_id"]),
                client_id=doc["client_id"],
                status=doc["status"],
                metadata=DocumentMetadata(**doc["metadata"]),
                status_reason=doc.get("status_reason")
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Document retrieval failed: {str(e)}")
    
    async def delete_document(
        self,
        client_id: str,
        document_id: str
    ) -> None:
        """Delete/archive a document.
        
        Args:
            client_id: Client's unique identifier
            document_id: Document's unique identifier
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            # Find document to get file_id
            doc = await self.documents_collection.find_one({
                "_id": ObjectId(document_id),
                "client_id": client_id
            })
            
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Delete from GridFS
            await self.fs.delete(doc["file_id"])
            
            # Delete metadata
            result = await self.documents_collection.delete_one({
                "_id": ObjectId(document_id),
                "client_id": client_id
            })
            
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Document not found")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Document deletion failed: {str(e)}") 