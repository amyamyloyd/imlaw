"""Version Control Service for managing form metadata versions.

This service provides functionality to manage and track different versions of form metadata,
including version creation, activation/deactivation, comparison, and retrieval.

Key Features:
- Version metadata storage and retrieval
- Active version management
- Version comparison and diff generation
- Support for version history tracking

Example Usage:
    version_service = VersionControlService()
    
    # Create a new version
    version = FormVersion(
        form_type="i485",
        version="2024",
        effective_date=datetime.utcnow()
    )
    version_id = await version_service.create_version(version)
    
    # Get active version
    active = await version_service.get_active_version("i485")
    
    # Compare versions
    diff = await version_service.compare_versions("i485", "2023", "2024")
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from src.db.database import Database
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
        """Initialize the service with MongoDB connection."""
        database = Database()
        self.db = database.db
        self.versions_collection = self.db['form_versions']
    
    async def create_version(self, version: FormVersion) -> str:
        """Create a new form version.
        
        If the version is marked as active, all other versions of the same form type
        will be automatically deactivated.
        
        Args:
            version (FormVersion): The version metadata to create
            
        Returns:
            str: The ID of the created version
            
        Example:
            version = FormVersion(
                form_type="i485",
                version="2024",
                effective_date=datetime.utcnow()
            )
            version_id = await service.create_version(version)
        """
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
        """Get specific version metadata.
        
        Args:
            form_type (str): The type of form (e.g., "i485")
            version (str): The version identifier (e.g., "2024")
            
        Returns:
            Optional[FormVersion]: The version metadata if found, None otherwise
            
        Example:
            version = await service.get_version("i485", "2024")
            if version:
                print(f"Version {version.version} is active: {version.is_active}")
        """
        result = await self.versions_collection.find_one({
            'form_type': form_type,
            'version': version
        })
        return FormVersion(**result) if result else None
    
    async def get_active_version(self, form_type: str) -> Optional[FormVersion]:
        """Get the currently active version for a form type.
        
        Args:
            form_type (str): The type of form to get the active version for
            
        Returns:
            Optional[FormVersion]: The active version if found, None otherwise
            
        Example:
            active = await service.get_active_version("i485")
            if active:
                print(f"Active version is {active.version}")
        """
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
        """List all versions for a form type.
        
        Args:
            form_type (str): The type of form to list versions for
            include_inactive (bool, optional): Whether to include inactive versions.
                Defaults to False.
                
        Returns:
            List[FormVersion]: List of versions, sorted by effective date descending
            
        Example:
            versions = await service.list_versions("i485", include_inactive=True)
            for v in versions:
                print(f"Version {v.version}: Active={v.is_active}")
        """
        query = {'form_type': form_type}
        if not include_inactive:
            query['is_active'] = True
            
        cursor = self.versions_collection.find(query).sort('effective_date', -1)
        results = await cursor.to_list(length=None)
        return [FormVersion(**result) for result in results]
    
    async def deactivate_versions(self, form_type: str) -> None:
        """Deactivate all versions for a form type.
        
        Args:
            form_type (str): The type of form to deactivate versions for
            
        Example:
            await service.deactivate_versions("i485")
        """
        await self.versions_collection.update_many(
            {'form_type': form_type},
            {'$set': {'is_active': False}}
        )
    
    async def activate_version(
        self,
        form_type: str,
        version: str
    ) -> bool:
        """Activate a specific version and deactivate all others.
        
        Args:
            form_type (str): The type of form
            version (str): The version identifier to activate
            
        Returns:
            bool: True if version was activated, False if version not found
            
        Example:
            success = await service.activate_version("i485", "2024")
            if success:
                print("Version activated successfully")
        """
        # First check if version exists
        existing = await self.get_version(form_type, version)
        if not existing:
            return False
            
        # Deactivate all versions
        await self.deactivate_versions(form_type)
        
        # Activate the specified version
        result = await self.versions_collection.update_one(
            {
                'form_type': form_type,
                'version': version
            },
            {'$set': {'is_active': True}}
        )
        return result.modified_count > 0
    
    async def compare_versions(
        self,
        form_type: str,
        version1: str,
        version2: str
    ) -> Optional[Dict[str, Any]]:
        """Compare two versions and return their differences.
        
        Args:
            form_type (str): The type of form
            version1 (str): First version identifier
            version2 (str): Second version identifier
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing:
                - metadata_changes: Changes in metadata fields
                - field_changes: List of changed field IDs
                - version1_date: Effective date of first version
                - version2_date: Effective date of second version
                - newer_version: Which version is newer
                Returns None if either version not found
                
        Example:
            diff = await service.compare_versions("i485", "2023", "2024")
            if diff:
                print(f"Changed fields: {diff['field_changes']}")
                print(f"Newer version: {diff['newer_version']}")
        """
        v1 = await self.get_version(form_type, version1)
        v2 = await self.get_version(form_type, version2)
        
        if not v1 or not v2:
            return None
            
        # Compare metadata
        metadata_changes = {}
        for key in set(v1.metadata.keys()) | set(v2.metadata.keys()):
            old_value = v1.metadata.get(key)
            new_value = v2.metadata.get(key)
            if old_value != new_value:
                metadata_changes[key] = {
                    'type': 'added' if old_value is None else 'removed' if new_value is None else 'modified',
                    'old_value': old_value,
                    'new_value': new_value
                }
        
        # Compare changes lists
        field_changes = []
        for change in v2.changes:
            if change not in v1.changes:
                field_changes.append(change.get('field_id'))
        
        return {
            'metadata_changes': metadata_changes,
            'field_changes': field_changes,
            'version1_date': v1.effective_date,
            'version2_date': v2.effective_date,
            'newer_version': version2 if v2.effective_date > v1.effective_date else version1
        } 