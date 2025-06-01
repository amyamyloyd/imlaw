from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

from src.config.database import Database
from src.models.form_schema import FormSchema, FormFieldDefinition

class PDFStorageService:
    """Service for storing PDF form field definitions and metadata in MongoDB"""
    
    def __init__(self):
        self.db = Database.get_db()
    
    def store_form_fields(
        self,
        form_type: str,
        version: str,
        fields: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store extracted form fields and metadata in MongoDB
        
        Args:
            form_type: Type/identifier of the form (e.g., 'i485')
            version: Version of the form (e.g., '2024')
            fields: List of extracted field definitions
            metadata: Optional additional form metadata
            
        Returns:
            ID of the created FormSchema document
        """
        # Convert raw field data to FormFieldDefinition objects
        field_definitions = []
        for field_data in fields:
            field_def = FormFieldDefinition(
                field_id=field_data["id"],
                field_type=field_data["type"],
                label=field_data.get("label", ""),
                required=field_data.get("required", False),
                tooltip=field_data.get("tooltip", ""),
                properties=field_data.get("properties", {}),
                page_number=field_data.get("page", None),
                default_value=field_data.get("default", None)
            )
            field_definitions.append(field_def)
        
        # Create FormSchema document
        form_schema = FormSchema(
            form_type=form_type,
            version=version,
            fields=field_definitions,
            total_fields=len(field_definitions),
            metadata=metadata or {},
            created_at=datetime.now(UTC)
        )
        
        # Check if form version already exists
        existing = self.db.form_schemas.find_one({
            "form_type": form_type,
            "version": version
        })
        
        if existing:
            # Update existing schema
            self.db.form_schemas.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "fields": [f.model_dump() for f in field_definitions],
                    "total_fields": len(field_definitions),
                    "metadata": metadata or {},
                    "updated_at": datetime.now(UTC)
                }}
            )
            return str(existing["_id"])
        else:
            # Insert new schema
            result = self.db.form_schemas.insert_one(form_schema.model_dump())
            return str(result.inserted_id)
    
    def get_form_fields(self, form_type: str, version: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored form field definitions
        
        Args:
            form_type: Type/identifier of the form
            version: Version of the form
            
        Returns:
            FormSchema document if found, None otherwise
        """
        return self.db.form_schemas.find_one({
            "form_type": form_type,
            "version": version
        })
    
    def delete_form_schema(self, form_type: str, version: str) -> bool:
        """
        Delete a stored form schema
        
        Args:
            form_type: Type/identifier of the form
            version: Version of the form
            
        Returns:
            True if deleted, False if not found
        """
        result = self.db.form_schemas.delete_one({
            "form_type": form_type,
            "version": version
        })
        return result.deleted_count > 0 