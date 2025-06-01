import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.pdf_storage_service import PDFStorageService

def test_pdf_storage():
    """Test PDF field storage and retrieval"""
    service = PDFStorageService()
    
    # Test data
    test_fields = [
        {
            "id": "name_given",
            "type": "text",
            "label": "Given Name",
            "required": True,
            "tooltip": "Enter your legal first name",
            "page": 1,
            "properties": {
                "maxLength": 50,
                "pattern": "^[a-zA-Z\\s-']*$"
            }
        },
        {
            "id": "name_family",
            "type": "text",
            "label": "Family Name",
            "required": True,
            "tooltip": "Enter your legal last name",
            "page": 1,
            "properties": {
                "maxLength": 50,
                "pattern": "^[a-zA-Z\\s-']*$"
            }
        }
    ]
    
    test_metadata = {
        "form_title": "Application to Register Permanent Residence",
        "form_description": "Use this application to apply for permanent residence",
        "total_pages": 18
    }
    
    print("\nTesting PDF Storage Service:")
    
    # Test storing fields
    form_id = service.store_form_fields(
        form_type="i485",
        version="2024",
        fields=test_fields,
        metadata=test_metadata
    )
    print(f"Stored form schema with ID: {form_id}")
    
    # Test retrieving fields
    stored_schema = service.get_form_fields("i485", "2024")
    print(f"\nRetrieved schema: {stored_schema}")
    
    # Test updating fields
    updated_fields = test_fields.copy()
    updated_fields[0]["tooltip"] = "Updated tooltip for testing"
    
    updated_id = service.store_form_fields(
        form_type="i485",
        version="2024",
        fields=updated_fields,
        metadata=test_metadata
    )
    print(f"\nUpdated schema with ID: {updated_id}")
    
    # Verify update
    updated_schema = service.get_form_fields("i485", "2024")
    print(f"\nVerified update - new tooltip: {updated_schema['fields'][0]['tooltip']}")
    
    # Test deletion
    deleted = service.delete_form_schema("i485", "2024")
    print(f"\nDeleted schema: {deleted}")
    
    # Verify deletion
    deleted_schema = service.get_form_fields("i485", "2024")
    print(f"Verified deletion - schema exists: {deleted_schema is not None}")

if __name__ == "__main__":
    test_pdf_storage() 