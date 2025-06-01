from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from database import Database
from bson import ObjectId

class FormVersion(BaseModel):
    """Form version metadata"""
    form_type: str = Field(..., description="Type of form (e.g., i485, i130)")
    version: str = Field(..., description="Version identifier (e.g., '2024')")
    effective_date: datetime = Field(..., description="When this version became effective")
    expiration_date: Optional[datetime] = Field(None, description="When this version expires")
    changes: List[Dict[str, Any]] = Field(default_factory=list, description="List of changes from previous version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional version metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True, description="Whether this version is currently active")

class VersionControlService:
    """Service for managing form metadata versions"""
    
    def __init__(self):
        self.db = Database.get_db()
        self.versions_collection = self.db['form_versions']
    
    async def create_version(self, version: FormVersion) -> str:
        """Create a new form version"""
        # If this is marked as active, deactivate other versions
        if version.is_active:
            await self.deactivate_versions(version.form_type)
            
        version_dict = version.model_dump()
        result = await self.versions_collection.insert_one(version_dict)
        return str(result.inserted_id)
    
    async def get_version(
        self,
        form_type: str,
        version: str
    ) -> Optional[FormVersion]:
        """Get specific version metadata"""
        result = await self.versions_collection.find_one({
            'form_type': form_type,
            'version': version
        })
        return FormVersion(**result) if result else None
    
    async def get_active_version(self, form_type: str) -> Optional[FormVersion]:
        """Get the currently active version for a form type"""
        result = await self.versions_collection.find_one({
            'form_type': form_type,
            'is_active': True
        })
        return FormVersion(**result) if result else None
    
    async def list_versions(
        self,
        form_type: str,
        include_inactive: bool = False
    ) -> List[FormVersion]:
        """List all versions for a form type"""
        query = {'form_type': form_type}
        if not include_inactive:
            query['is_active'] = True
            
        cursor = self.versions_collection.find(query).sort('effective_date', -1)
        results = await cursor.to_list(length=None)
        return [FormVersion(**result) for result in results]
    
    async def update_version(
        self,
        form_type: str,
        version: str,
        changes: Dict[str, Any]
    ) -> bool:
        """Update version metadata"""
        changes['updated_at'] = datetime.utcnow()
        result = await self.versions_collection.update_one(
            {
                'form_type': form_type,
                'version': version
            },
            {'$set': changes}
        )
        return result.modified_count > 0
    
    async def deactivate_versions(self, form_type: str) -> int:
        """Deactivate all versions for a form type"""
        result = await self.versions_collection.update_many(
            {
                'form_type': form_type,
                'is_active': True
            },
            {
                '$set': {
                    'is_active': False,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        return result.modified_count
    
    async def activate_version(
        self,
        form_type: str,
        version: str
    ) -> bool:
        """Activate a specific version and deactivate others"""
        # First deactivate all versions
        await self.deactivate_versions(form_type)
        
        # Then activate the specified version
        result = await self.versions_collection.update_one(
            {
                'form_type': form_type,
                'version': version
            },
            {
                '$set': {
                    'is_active': True,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def compare_versions(
        self,
        form_type: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """Compare two versions and return differences"""
        v1 = await self.get_version(form_type, version1)
        v2 = await self.get_version(form_type, version2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
            
        # Compare metadata and changes
        differences = {
            'metadata_changes': self._compare_dicts(v1.metadata, v2.metadata),
            'field_changes': [],
            'version1_date': v1.effective_date,
            'version2_date': v2.effective_date,
            'newer_version': version1 if v1.effective_date > v2.effective_date else version2
        }
        
        # Add field changes from both versions
        all_changes = set()
        if v1.changes:
            all_changes.update(self._extract_field_changes(v1.changes))
        if v2.changes:
            all_changes.update(self._extract_field_changes(v2.changes))
        
        differences['field_changes'] = sorted(list(all_changes))
        return differences
    
    def _compare_dicts(self, dict1: Dict, dict2: Dict) -> Dict[str, Any]:
        """Compare two dictionaries and return differences"""
        changes = {}
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        for key in all_keys:
            if key not in dict1:
                changes[key] = {'type': 'added', 'value': dict2[key]}
            elif key not in dict2:
                changes[key] = {'type': 'removed', 'value': dict1[key]}
            elif dict1[key] != dict2[key]:
                changes[key] = {
                    'type': 'modified',
                    'old_value': dict1[key],
                    'new_value': dict2[key]
                }
                
        return changes
    
    def _extract_field_changes(self, changes: List[Dict]) -> set:
        """Extract unique field changes from a list of changes"""
        field_changes = set()
        for change in changes:
            if 'field_id' in change:
                field_changes.add(change['field_id'])
        return field_changes 