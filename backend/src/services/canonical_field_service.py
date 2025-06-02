from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from models.canonical_field import CanonicalField, FormFieldMapping, ValidationRule, ValidationHistory
from config.database import Database
from models.canonical_field_collection import CanonicalFieldCollection

class CanonicalFieldService:
    """Service for managing canonical field definitions"""
    
    def __init__(self, db=None):
        """Initialize service with optional database instance"""
        self.db = db or Database.get_db()
        self.collection = CanonicalFieldCollection()
        self.fields = self.db[self.collection.name]
    
    async def create_field(self, field: CanonicalField) -> str:
        """Create a new canonical field"""
        try:
            # Ensure timestamps are set
            field.created_at = datetime.utcnow()
            field.updated_at = field.created_at
            
            # Initialize usage stats
            if not field.usage_stats:
                field.usage_stats = {
                    "total_uses": 0,
                    "error_count": 0,
                    "form_usage": {},
                    "last_used": None
                }
            
            # Convert to dict and insert
            field_dict = field.model_dump()
            result = await self.fields.insert_one(field_dict)
            return str(result.inserted_id)
            
        except Exception as e:
            # Handle duplicate field_name error specifically
            if "duplicate key error" in str(e) and "field_name" in str(e):
                raise ValueError(f"Field name '{field.field_name}' already exists")
            raise
    
    async def get_field(self, field_name: str) -> Optional[CanonicalField]:
        """Get a canonical field by its name"""
        result = await self.fields.find_one({"field_name": field_name})
        return CanonicalField(**result) if result else None
    
    async def get_fields(
        self,
        category: Optional[str] = None,
        group_name: Optional[str] = None,
        data_type: Optional[str] = None,
        include_inactive: bool = False,
        page: int = 1,
        page_size: int = 50
    ) -> List[CanonicalField]:
        """Get canonical fields with optional filtering"""
        # Build query
        query = {}
        if category:
            query["category"] = category
        if group_name:
            query["group_name"] = group_name
        if data_type:
            query["data_type"] = data_type
        if not include_inactive:
            query["active"] = True
            
        # Execute query with pagination
        skip = (page - 1) * page_size
        cursor = self.fields.find(query).skip(skip).limit(page_size)
        results = await cursor.to_list(length=page_size)
        
        return [CanonicalField(**result) for result in results]
    
    async def search_fields(
        self,
        search_text: str,
        exact_match: bool = False
    ) -> List[CanonicalField]:
        """Search canonical fields by name, aliases, or display name"""
        if exact_match:
            query = {
                "$or": [
                    {"field_name": search_text},
                    {"aliases": search_text},
                    {"display_name": search_text}
                ]
            }
        else:
            # Case-insensitive partial match
            pattern = f".*{search_text}.*"
            query = {
                "$or": [
                    {"field_name": {"$regex": pattern, "$options": "i"}},
                    {"aliases": {"$regex": pattern, "$options": "i"}},
                    {"display_name": {"$regex": pattern, "$options": "i"}}
                ]
            }
        
        results = await self.fields.find(query).to_list(length=50)
        return [CanonicalField(**result) for result in results]
    
    async def update_field(
        self,
        field_name: str,
        updates: Dict[str, Any],
        changed_by: str
    ) -> bool:
        """Update a canonical field"""
        # Don't allow changing field_name through updates
        if "field_name" in updates:
            del updates["field_name"]
        
        # Track validation rule changes if present
        if "validation_rules" in updates:
            current = await self.get_field(field_name)
            if current:
                history_entry = ValidationHistory(
                    changed_by=changed_by,
                    previous_rules=current.validation_rules,
                    new_rules=updates["validation_rules"]
                )
                updates["validation_history"] = current.validation_history + [history_entry]
        
        # Set updated timestamp
        updates["updated_at"] = datetime.utcnow()
        
        result = await self.fields.update_one(
            {"field_name": field_name},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def delete_field(self, field_name: str) -> bool:
        """Delete a canonical field"""
        # First check if field is used in any mappings
        field = await self.get_field(field_name)
        if field and field.form_mappings:
            raise ValueError(
                f"Cannot delete field '{field_name}' as it has {len(field.form_mappings)} "
                "active form mappings. Remove mappings first."
            )
        
        result = await self.fields.delete_one({"field_name": field_name})
        return result.deleted_count > 0
    
    async def add_form_mapping(
        self,
        field_name: str,
        mapping: FormFieldMapping
    ) -> bool:
        """Add a form field mapping to a canonical field"""
        # Ensure timestamps are set
        mapping.created_at = datetime.utcnow()
        mapping.updated_at = mapping.created_at
        
        # Add mapping and update usage stats
        result = await self.fields.update_one(
            {"field_name": field_name},
            {
                "$push": {"form_mappings": mapping.model_dump()},
                "$inc": {"usage_stats.total_uses": 1},
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "usage_stats.last_used": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def remove_form_mapping(
        self,
        field_name: str,
        form_type: str,
        form_version: str,
        field_id: str
    ) -> bool:
        """Remove a form field mapping from a canonical field"""
        result = await self.fields.update_one(
            {"field_name": field_name},
            {
                "$pull": {
                    "form_mappings": {
                        "form_type": form_type,
                        "form_version": form_version,
                        "field_id": field_id
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    async def get_fields_by_form(
        self,
        form_type: str,
        form_version: str
    ) -> List[CanonicalField]:
        """Get all canonical fields mapped to a specific form version"""
        query = {
            "form_mappings": {
                "$elemMatch": {
                    "form_type": form_type,
                    "form_version": form_version
                }
            }
        }
        results = await self.fields.find(query).to_list(length=None)
        return [CanonicalField(**result) for result in results]
    
    async def increment_error_count(self, field_name: str) -> bool:
        """Increment the error count for a field"""
        result = await self.fields.update_one(
            {"field_name": field_name},
            {
                "$inc": {
                    "usage_stats.error_count": 1,
                    "usage_stats.total_uses": 1
                },
                "$set": {
                    "usage_stats.last_used": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def record_usage(
        self,
        field_name: str,
        form_type: Optional[str] = None
    ) -> bool:
        """Record usage of a field"""
        update = {
            "$inc": {"usage_stats.total_uses": 1},
            "$set": {
                "usage_stats.last_used": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
        
        if form_type:
            update["$inc"][f"usage_stats.form_usage.{form_type}"] = 1
        
        result = await self.fields.update_one(
            {"field_name": field_name},
            update
        )
        return result.modified_count > 0 