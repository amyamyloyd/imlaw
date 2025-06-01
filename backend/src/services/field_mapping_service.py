from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from database import Database

class FieldMapping(BaseModel):
    """Mapping between form-specific field IDs and canonical field names"""
    form_type: str = Field(..., description="Type of form (e.g., i485, i130)")
    form_version: str = Field(..., description="Form version")
    field_id: str = Field(..., description="Original field ID from the form")
    canonical_name: str = Field(..., description="Standardized canonical field name")
    description: Optional[str] = Field(None, description="Description of what this field represents")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict, description="Additional mapping metadata")

class FieldMappingService:
    """Service for managing field name standardization and mapping"""
    
    def __init__(self):
        self.db = Database.get_db()
        self.mappings_collection = self.db['field_mappings']
    
    async def create_mapping(self, mapping: FieldMapping) -> str:
        """Create a new field mapping"""
        mapping_dict = mapping.model_dump()
        result = await self.mappings_collection.insert_one(mapping_dict)
        return str(result.inserted_id)
    
    async def get_mapping(
        self,
        form_type: str,
        form_version: str,
        field_id: str
    ) -> Optional[FieldMapping]:
        """Get mapping for a specific field"""
        result = await self.mappings_collection.find_one({
            'form_type': form_type,
            'form_version': form_version,
            'field_id': field_id
        })
        return FieldMapping(**result) if result else None
    
    async def get_form_mappings(
        self,
        form_type: str,
        form_version: str
    ) -> List[FieldMapping]:
        """Get all mappings for a specific form version"""
        cursor = self.mappings_collection.find({
            'form_type': form_type,
            'form_version': form_version
        })
        results = await cursor.to_list(length=None)
        return [FieldMapping(**result) for result in results]
    
    async def update_mapping(
        self,
        form_type: str,
        form_version: str,
        field_id: str,
        canonical_name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update an existing field mapping"""
        update_data = {
            'canonical_name': canonical_name,
            'updated_at': datetime.utcnow()
        }
        if description is not None:
            update_data['description'] = description
        if metadata is not None:
            update_data['metadata'] = metadata
            
        result = await self.mappings_collection.update_one(
            {
                'form_type': form_type,
                'form_version': form_version,
                'field_id': field_id
            },
            {'$set': update_data}
        )
        return result.modified_count > 0
    
    async def delete_mapping(
        self,
        form_type: str,
        form_version: str,
        field_id: str
    ) -> bool:
        """Delete a field mapping"""
        result = await self.mappings_collection.delete_one({
            'form_type': form_type,
            'form_version': form_version,
            'field_id': field_id
        })
        return result.deleted_count > 0
    
    async def get_canonical_name(
        self,
        form_type: str,
        form_version: str,
        field_id: str
    ) -> Optional[str]:
        """Get canonical name for a field if mapping exists"""
        mapping = await self.get_mapping(form_type, form_version, field_id)
        return mapping.canonical_name if mapping else None
    
    async def bulk_create_mappings(
        self,
        mappings: List[FieldMapping]
    ) -> List[str]:
        """Create multiple field mappings at once"""
        mapping_dicts = [mapping.model_dump() for mapping in mappings]
        result = await self.mappings_collection.insert_many(mapping_dicts)
        return [str(id) for id in result.inserted_ids]
    
    async def find_unmapped_fields(
        self,
        form_type: str,
        form_version: str,
        field_ids: List[str]
    ) -> List[str]:
        """Find field IDs that don't have mappings"""
        existing_mappings = await self.get_form_mappings(form_type, form_version)
        mapped_ids = {mapping.field_id for mapping in existing_mappings}
        return [field_id for field_id in field_ids if field_id not in mapped_ids] 