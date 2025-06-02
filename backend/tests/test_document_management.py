"""Tests for document management system."""
import pytest
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io
from datetime import datetime
from bson import ObjectId

from src.main import app
from src.models.document import DocumentStatus, DocumentMetadata, DocumentResponse
from src.services.document_tracking_service import DocumentTrackingService

client = TestClient(app)

@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing."""
    return io.BytesIO(b"Sample PDF content")

@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "client_id": "test_client_123",
        "document_type": "passport",
        "description": "Test passport document",
        "metadata": {
            "country": "USA",
            "expiry_date": "2025-12-31"
        }
    }

@pytest.fixture
async def uploaded_document(sample_document_data):
    """Create a test document in the database."""
    service = DocumentTrackingService()
    doc = await service.upload_document(
        client_id=sample_document_data["client_id"],
        file_name="test.pdf",
        content_type="application/pdf",
        file_content=b"Test content",
        document_type=sample_document_data["document_type"],
        description=sample_document_data["description"],
        metadata=sample_document_data["metadata"]
    )
    return doc

# Route Tests

def test_upload_document(sample_pdf, sample_document_data):
    """Test document upload endpoint."""
    files = {"file": ("test.pdf", sample_pdf, "application/pdf")}
    data = {
        "document_type": sample_document_data["document_type"],
        "description": sample_document_data["description"],
        "metadata": sample_document_data["metadata"]
    }
    
    response = client.post(
        f"/api/v1/clients/{sample_document_data['client_id']}/documents",
        files=files,
        data=data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == sample_document_data["client_id"]
    assert data["status"] == DocumentStatus.PENDING
    assert data["metadata"]["document_type"] == sample_document_data["document_type"]

def test_update_document_status(uploaded_document, sample_document_data):
    """Test document status update endpoint."""
    status_update = {
        "status": DocumentStatus.APPROVED,
        "reason": "Document verified"
    }
    
    response = client.put(
        f"/api/v1/clients/{sample_document_data['client_id']}/documents/{uploaded_document.id}/status",
        json=status_update
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == DocumentStatus.APPROVED
    assert data["status_reason"] == "Document verified"

def test_get_documents(uploaded_document, sample_document_data):
    """Test get documents endpoint."""
    response = client.get(
        f"/api/v1/clients/{sample_document_data['client_id']}/documents"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(doc["id"] == uploaded_document.id for doc in data)

def test_get_documents_with_filters(uploaded_document, sample_document_data):
    """Test get documents endpoint with filters."""
    response = client.get(
        f"/api/v1/clients/{sample_document_data['client_id']}/documents",
        params={
            "status": DocumentStatus.PENDING,
            "document_type": sample_document_data["document_type"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(doc["status"] == DocumentStatus.PENDING for doc in data)
    assert all(doc["metadata"]["document_type"] == sample_document_data["document_type"] for doc in data)

def test_get_document(uploaded_document, sample_document_data):
    """Test get specific document endpoint."""
    response = client.get(
        f"/api/v1/clients/{sample_document_data['client_id']}/documents/{uploaded_document.id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == uploaded_document.id
    assert data["client_id"] == sample_document_data["client_id"]

def test_get_nonexistent_document(sample_document_data):
    """Test get document endpoint with non-existent ID."""
    fake_id = str(ObjectId())
    response = client.get(
        f"/api/v1/clients/{sample_document_data['client_id']}/documents/{fake_id}"
    )
    
    assert response.status_code == 404

def test_delete_document(uploaded_document, sample_document_data):
    """Test document deletion endpoint."""
    response = client.delete(
        f"/api/v1/clients/{sample_document_data['client_id']}/documents/{uploaded_document.id}"
    )
    
    assert response.status_code == 200
    
    # Verify document is deleted
    get_response = client.get(
        f"/api/v1/clients/{sample_document_data['client_id']}/documents/{uploaded_document.id}"
    )
    assert get_response.status_code == 404

# Service Tests

@pytest.mark.asyncio
async def test_document_service_upload():
    """Test DocumentTrackingService upload_document method."""
    service = DocumentTrackingService()
    file_content = b"Test content"
    
    doc = await service.upload_document(
        client_id="test_client",
        file_name="test.pdf",
        content_type="application/pdf",
        file_content=file_content,
        document_type="passport",
        description="Test document",
        metadata={"test": "data"}
    )
    
    assert isinstance(doc, DocumentResponse)
    assert doc.client_id == "test_client"
    assert doc.status == DocumentStatus.PENDING
    assert doc.metadata.document_type == "passport"
    assert doc.metadata.file_size == len(file_content)

@pytest.mark.asyncio
async def test_document_service_status_update():
    """Test DocumentTrackingService update_document_status method."""
    service = DocumentTrackingService()
    
    # First upload a document
    doc = await service.upload_document(
        client_id="test_client",
        file_name="test.pdf",
        content_type="application/pdf",
        file_content=b"Test content",
        document_type="passport"
    )
    
    # Update its status
    updated_doc = await service.update_document_status(
        client_id="test_client",
        document_id=doc.id,
        status=DocumentStatus.APPROVED,
        reason="Verified"
    )
    
    assert updated_doc.status == DocumentStatus.APPROVED
    assert updated_doc.status_reason == "Verified"

@pytest.mark.asyncio
async def test_document_service_get_documents():
    """Test DocumentTrackingService get_client_documents method."""
    service = DocumentTrackingService()
    client_id = "test_client_get"
    
    # Upload multiple documents
    doc1 = await service.upload_document(
        client_id=client_id,
        file_name="test1.pdf",
        content_type="application/pdf",
        file_content=b"Test content 1",
        document_type="passport"
    )
    
    doc2 = await service.upload_document(
        client_id=client_id,
        file_name="test2.pdf",
        content_type="application/pdf",
        file_content=b"Test content 2",
        document_type="birth_certificate"
    )
    
    # Test getting all documents
    docs = await service.get_client_documents(client_id)
    assert len(docs) >= 2
    assert any(d.id == doc1.id for d in docs)
    assert any(d.id == doc2.id for d in docs)
    
    # Test filtering by document type
    passport_docs = await service.get_client_documents(
        client_id,
        document_type="passport"
    )
    assert len(passport_docs) >= 1
    assert all(d.metadata.document_type == "passport" for d in passport_docs)

@pytest.mark.asyncio
async def test_document_service_delete():
    """Test DocumentTrackingService delete_document method."""
    service = DocumentTrackingService()
    
    # First upload a document
    doc = await service.upload_document(
        client_id="test_client",
        file_name="test.pdf",
        content_type="application/pdf",
        file_content=b"Test content",
        document_type="passport"
    )
    
    # Delete it
    await service.delete_document(
        client_id="test_client",
        document_id=doc.id
    )
    
    # Verify it's deleted
    deleted_doc = await service.get_document(
        client_id="test_client",
        document_id=doc.id
    )
    assert deleted_doc is None 