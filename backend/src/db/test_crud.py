from datetime import datetime, UTC
from ..config.database import Database
from ..models.form_schema import FormSchema, FormFieldDefinition
from ..models.canonical_field import CanonicalField, FormFieldMapping
from ..models.client_entry import ClientEntry, FormEntry

def test_form_schema_crud():
    """Test CRUD operations for FormSchema collection"""
    db = Database.get_db()
    
    # Create
    test_field = FormFieldDefinition(
        field_id="name_given",
        label="Given Name",
        field_type="text",
        required=True,
        tooltip="Enter your legal first name"
    )
    
    test_schema = FormSchema(
        form_type="i485",
        version="2024",
        fields=[test_field],
        total_fields=1,
        created_at=datetime.now(UTC)
    )
    
    result = db.form_schemas.insert_one(test_schema.model_dump())
    print(f"Created FormSchema with id: {result.inserted_id}")
    
    # Read
    found = db.form_schemas.find_one({"form_type": "i485", "version": "2024"})
    print(f"Found FormSchema: {found}")
    
    # Update
    update_result = db.form_schemas.update_one(
        {"_id": result.inserted_id},
        {"$set": {"fields.0.tooltip": "Updated tooltip"}}
    )
    print(f"Updated FormSchema: {update_result.modified_count} document(s)")
    
    # Delete
    delete_result = db.form_schemas.delete_one({"_id": result.inserted_id})
    print(f"Deleted FormSchema: {delete_result.deleted_count} document(s)")

def test_canonical_field_crud():
    """Test CRUD operations for CanonicalField collection"""
    db = Database.get_db()
    
    # Create
    test_mapping = FormFieldMapping(
        form_type="i485",
        form_version="2024",
        field_id="name_given",
        field_ids=["name_given", "first_name"]
    )
    
    test_canonical = CanonicalField(
        field_name="given_name",
        display_name="Given Name",
        data_type="string",
        category="personal",
        validation_regex=r"^[a-zA-Z\s-']{1,50}$",
        form_mappings=[test_mapping],
        created_at=datetime.now(UTC)
    )
    
    result = db.canonical_fields.insert_one(test_canonical.model_dump())
    print(f"Created CanonicalField with id: {result.inserted_id}")
    
    # Read
    found = db.canonical_fields.find_one({"field_name": "given_name"})
    print(f"Found CanonicalField: {found}")
    
    # Update
    update_result = db.canonical_fields.update_one(
        {"_id": result.inserted_id},
        {"$set": {"category": "identity"}}
    )
    print(f"Updated CanonicalField: {update_result.modified_count} document(s)")
    
    # Delete
    delete_result = db.canonical_fields.delete_one({"_id": result.inserted_id})
    print(f"Deleted CanonicalField: {delete_result.deleted_count} document(s)")

def test_client_entry_crud():
    """Test CRUD operations for ClientEntry collection"""
    db = Database.get_db()
    
    # Create
    test_form = FormEntry(
        form_type="i485",
        form_version="2024",
        field_data={
            "name_given": "John",
            "name_family": "Doe"
        },
        created_at=datetime.now(UTC)
    )
    
    test_client = ClientEntry(
        client_id="TEST123",
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        date_of_birth=datetime(1990, 1, 1, tzinfo=UTC),
        forms=[test_form],
        created_at=datetime.now(UTC)
    )
    
    result = db.client_entries.insert_one(test_client.model_dump())
    print(f"Created ClientEntry with id: {result.inserted_id}")
    
    # Read
    found = db.client_entries.find_one({"client_id": "TEST123"})
    print(f"Found ClientEntry: {found}")
    
    # Update
    update_result = db.client_entries.update_one(
        {"_id": result.inserted_id},
        {"$set": {"email": "updated@example.com"}}
    )
    print(f"Updated ClientEntry: {update_result.modified_count} document(s)")
    
    # Delete
    delete_result = db.client_entries.delete_one({"_id": result.inserted_id})
    print(f"Deleted ClientEntry: {delete_result.deleted_count} document(s)")

if __name__ == "__main__":
    print("\nTesting FormSchema CRUD operations:")
    test_form_schema_crud()
    
    print("\nTesting CanonicalField CRUD operations:")
    test_canonical_field_crud()
    
    print("\nTesting ClientEntry CRUD operations:")
    test_client_entry_crud()
    
    print("\nAll CRUD tests completed!") 