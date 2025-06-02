"""Test schema migration service"""
import pytest
from datetime import datetime
from src.services.schema_migration_service import SchemaMigrationService, MigrationStrategy
from src.models.form_schema import FormSchema, FormFieldDefinition, FieldType, Position, FieldFlags

@pytest.fixture
def migration_service():
    return SchemaMigrationService()

@pytest.fixture
def sample_form_data():
    return {
        "form1[0].#subform[0].FamilyName[0]": "Smith",
        "form1[0].#subform[0].GivenName[0]": "John",
        "form1[0].#subform[0].DateOfBirth[0]": "1990-01-01"
    }

@pytest.fixture
def sample_migration_strategy():
    return MigrationStrategy(
        field_mappings={
            "form1[0].#subform[0].FamilyName[0]": "form1[0].#subform[0].LastName[0]",
            "form1[0].#subform[0].GivenName[0]": "form1[0].#subform[0].FirstName[0]",
            "form1[0].#subform[0].DateOfBirth[0]": "form1[0].#subform[0].BirthDate[0]"
        },
        value_transformations={
            "form1[0].#subform[0].BirthDate[0]": {
                "format": {
                    "type": "date",
                    "from_format": "%Y-%m-%d",
                    "to_format": "%d/%m/%Y"
                }
            }
        },
        validation_updates={
            "form1[0].#subform[0].LastName[0]": {
                "type": "length",
                "max_length": 50
            }
        }
    )

def test_register_and_get_migration_strategy(migration_service, sample_migration_strategy):
    """Test registering and retrieving a migration strategy"""
    form_type = "I-485"
    from_version = "2024.1"
    to_version = "2024.2"
    
    # Initially no strategy exists
    assert migration_service.get_migration_strategy(form_type, from_version, to_version) is None
    
    # Register strategy
    migration_service.register_migration_strategy(form_type, from_version, to_version, sample_migration_strategy)
    
    # Retrieve strategy
    retrieved_strategy = migration_service.get_migration_strategy(form_type, from_version, to_version)
    assert retrieved_strategy is not None
    assert retrieved_strategy.field_mappings == sample_migration_strategy.field_mappings
    assert retrieved_strategy.value_transformations == sample_migration_strategy.value_transformations
    assert retrieved_strategy.validation_updates == sample_migration_strategy.validation_updates

def test_migrate_form_data(migration_service, sample_form_data, sample_migration_strategy):
    """Test migrating form data using a strategy"""
    form_type = "I-485"
    from_version = "2024.1"
    to_version = "2024.2"
    
    # Register strategy
    migration_service.register_migration_strategy(form_type, from_version, to_version, sample_migration_strategy)
    
    # Migrate data
    migrated_data = migration_service.migrate_form_data(form_type, from_version, to_version, sample_form_data)
    
    # Check field mappings
    assert "form1[0].#subform[0].LastName[0]" in migrated_data
    assert migrated_data["form1[0].#subform[0].LastName[0]"] == "Smith"
    assert "form1[0].#subform[0].FirstName[0]" in migrated_data
    assert migrated_data["form1[0].#subform[0].FirstName[0]"] == "John"
    
    # Check date format transformation
    assert migrated_data["form1[0].#subform[0].BirthDate[0]"] == "01/01/1990"

def test_migrate_form_data_with_validation(migration_service, sample_migration_strategy):
    """Test migrating form data with validation transformations"""
    form_type = "I-485"
    from_version = "2024.1"
    to_version = "2024.2"
    
    # Register strategy
    migration_service.register_migration_strategy(form_type, from_version, to_version, sample_migration_strategy)
    
    # Test data with long last name
    long_name_data = {
        "form1[0].#subform[0].FamilyName[0]": "A" * 100  # Name longer than max length
    }
    
    # Migrate data
    migrated_data = migration_service.migrate_form_data(form_type, from_version, to_version, long_name_data)
    
    # Check length validation
    assert len(migrated_data["form1[0].#subform[0].LastName[0]"]) == 50

def test_migrate_form_data_no_strategy(migration_service, sample_form_data):
    """Test migrating form data without a strategy raises an error"""
    form_type = "I-485"
    from_version = "2024.1"
    to_version = "2024.2"
    
    with pytest.raises(ValueError) as exc_info:
        migration_service.migrate_form_data(form_type, from_version, to_version, sample_form_data)
    
    assert "No migration strategy found" in str(exc_info.value)

def test_migrate_form_data_invalid_date(migration_service, sample_migration_strategy):
    """Test migrating form data with invalid date format"""
    form_type = "I-485"
    from_version = "2024.1"
    to_version = "2024.2"
    
    # Register strategy
    migration_service.register_migration_strategy(form_type, from_version, to_version, sample_migration_strategy)
    
    # Test data with invalid date
    invalid_date_data = {
        "form1[0].#subform[0].DateOfBirth[0]": "invalid-date"
    }
    
    # Migrate data - should not raise an error
    migrated_data = migration_service.migrate_form_data(form_type, from_version, to_version, invalid_date_data)
    
    # Original invalid value should be preserved
    assert migrated_data["form1[0].#subform[0].BirthDate[0]"] == "invalid-date" 