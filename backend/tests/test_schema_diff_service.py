"""Test schema diff service"""
import pytest
from datetime import datetime
from src.models.form_schema import FormSchema, FormFieldDefinition, FieldType, Position, FieldFlags
from src.models.versioned_form_schema import ChangeType
from src.services.schema_diff_service import SchemaDiffService

@pytest.fixture
def diff_service():
    return SchemaDiffService()

@pytest.fixture
def base_schema():
    fields = [
        FormFieldDefinition(
            field_id="form1[0].#subform[0].FamilyName[0]",
            field_type=FieldType.TEXT,
            field_name="Family Name",
            flags=FieldFlags(required=True),
            position=Position(x=50.0, y=100.0, width=200.0, height=20.0),
            properties={"maxLength": 50},
            page_number=1,
            tooltip="Enter your family name as it appears on your birth certificate"
        ),
        FormFieldDefinition(
            field_id="form1[0].#subform[0].GivenName[0]",
            field_type=FieldType.TEXT,
            field_name="Given Name",
            flags=FieldFlags(required=True),
            position=Position(x=50.0, y=150.0, width=200.0, height=20.0),
            properties={"maxLength": 50},
            page_number=1,
            tooltip="Enter your given name (first name)"
        )
    ]
    return FormSchema(
        form_type="I-485",
        version="2024.1",
        title="Application to Register Permanent Residence",
        fields=fields,
        total_fields=len(fields)
    )

@pytest.fixture
def modified_schema(base_schema):
    # Create a copy with modifications
    fields = [
        # Modified field
        FormFieldDefinition(
            field_id="form1[0].#subform[0].FamilyName[0]",
            field_type=FieldType.TEXT,
            field_name="Family Name (Last Name)",  # Name changed
            flags=FieldFlags(required=True),
            position=Position(x=50.0, y=100.0, width=200.0, height=20.0),
            properties={"maxLength": 100},  # Property changed
            page_number=1,
            tooltip="Enter your family name as it appears on your birth certificate"
        ),
        # Removed GivenName field
        # New field added
        FormFieldDefinition(
            field_id="form1[0].#subform[0].MiddleName[0]",
            field_type=FieldType.TEXT,
            field_name="Middle Name",
            flags=FieldFlags(required=False),
            position=Position(x=50.0, y=200.0, width=200.0, height=20.0),
            properties={"maxLength": 50},
            page_number=1,
            tooltip="Enter your middle name if you have one"
        )
    ]
    return FormSchema(
        form_type=base_schema.form_type,
        version="2024.2",
        title=base_schema.title,
        fields=fields,
        total_fields=len(fields)
    )

def test_detect_added_field(diff_service, base_schema, modified_schema):
    """Test that new fields are detected correctly"""
    diff = diff_service.calculate_diff(base_schema, modified_schema)
    
    # Find added field
    added = next(change for change in diff.changes 
                if change.change_type == ChangeType.ADDED)
    
    assert added.field_id == "form1[0].#subform[0].MiddleName[0]"
    assert added.previous_value is None
    assert added.new_value["field_name"] == "Middle Name"

def test_detect_removed_field(diff_service, base_schema, modified_schema):
    """Test that removed fields are detected correctly"""
    diff = diff_service.calculate_diff(base_schema, modified_schema)
    
    # Find removed field
    removed = next(change for change in diff.changes 
                  if change.change_type == ChangeType.REMOVED)
    
    assert removed.field_id == "form1[0].#subform[0].GivenName[0]"
    assert removed.new_value is None
    assert removed.previous_value["field_name"] == "Given Name"

def test_detect_modified_field(diff_service, base_schema, modified_schema):
    """Test that modified fields are detected correctly"""
    diff = diff_service.calculate_diff(base_schema, modified_schema)
    
    # Find modified field
    modified = next(change for change in diff.changes 
                   if change.change_type == ChangeType.MODIFIED)
    
    assert modified.field_id == "form1[0].#subform[0].FamilyName[0]"
    assert modified.previous_value["field_name"] == "Family Name"
    assert modified.new_value["field_name"] == "Family Name (Last Name)"
    assert modified.previous_value["properties"]["maxLength"] == 50
    assert modified.new_value["properties"]["maxLength"] == 100