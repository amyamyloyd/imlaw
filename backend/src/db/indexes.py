from ..config.database import Database

def create_indexes():
    """Create indexes for all collections"""
    db = Database.get_db()
    
    # Form Schemas Collection
    db.form_schemas.create_index([
        ("form_type", 1),
        ("version", 1)
    ], unique=True, name="unique_form_version")
    db.form_schemas.create_index("created_at")
    
    # Enhanced indexes for form metadata queries
    db.forms.create_index([
        ("form_type", 1),
        ("created_at", -1)
    ], name="form_type_date")
    
    db.forms.create_index([
        ("id", 1)
    ], unique=True, name="unique_form_id")
    
    db.forms.create_index([
        ("fields.field_type", 1),
        ("form_type", 1)
    ], name="field_type_lookup")
    
    db.forms.create_index([
        ("fields.field_id", 1)
    ], name="field_id_lookup")
    
    # Canonical Fields Collection
    db.canonical_fields.create_index("field_name", unique=True, name="unique_field_name")
    db.canonical_fields.create_index("category")
    db.canonical_fields.create_index([
        ("form_mappings.form_type", 1),
        ("form_mappings.form_version", 1)
    ], name="form_mappings")
    
    # Client Entries Collection
    db.client_entries.create_index("client_id", unique=True, name="unique_client_id")
    db.client_entries.create_index("email")
    db.client_entries.create_index([
        ("forms.form_type", 1),
        ("forms.form_version", 1)
    ], name="client_forms")
    db.client_entries.create_index("created_at")

if __name__ == "__main__":
    create_indexes()
    print("Successfully created all indexes") 