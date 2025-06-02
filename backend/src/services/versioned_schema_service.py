"""Versioned schema service"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId

from src.db.database import Database
from src.models.versioned_form_schema import (
    VersionedFormSchema,
    SchemaVersion,
    VersionDiff,
    FieldChange,
    VersionedFormSchemaCollection
)
from models.form_schema import FormSchema, FieldType

# Use a far future date for draft versions
UTC = timezone.utc
DRAFT_DATE = datetime(9999, 12, 31, tzinfo=UTC)

class VersionedSchemaService:
    """Service for managing versioned form schemas in MongoDB"""
    
    def __init__(self, db: Database):
        """Initialize the service with database connection"""
        self.db = db
        self.collection: Collection = self.db.get_collection(VersionedFormSchemaCollection.name)
        self._ensure_indexes()
        
    def _ensure_indexes(self):
        """Ensure required indexes exist in MongoDB"""
        for index in VersionedFormSchemaCollection.indexes:
            self.collection.create_index(**index)
            
    def _get_next_version(self, current: SchemaVersion, breaking_changes: bool = False) -> SchemaVersion:
        """Calculate the next version number based on changes"""
        if breaking_changes:
            return SchemaVersion(
                major=current.major + 1,
                minor=0,
                patch=0
            )
        return SchemaVersion(
            major=current.major,
            minor=current.minor + 1,
            patch=0
        )
        
    def _calculate_field_changes(self, old_schema: FormSchema, new_schema: FormSchema) -> List[FieldChange]:
        """Calculate changes between two schema versions"""
        changes = []
        old_fields = {f.field_id: f.dict() for f in old_schema.fields}
        new_fields = {f.field_id: f.dict() for f in new_schema.fields}
        
        # Find removed and modified fields
        for field_id, old_field in old_fields.items():
            if field_id not in new_fields:
                changes.append(FieldChange(
                    field_id=field_id,
                    change_type="removed",
                    previous_value=old_field
                ))
            elif new_fields[field_id] != old_field:
                changes.append(FieldChange(
                    field_id=field_id,
                    change_type="modified",
                    previous_value=old_field,
                    new_value=new_fields[field_id]
                ))
                
        # Find added fields
        for field_id, new_field in new_fields.items():
            if field_id not in old_fields:
                changes.append(FieldChange(
                    field_id=field_id,
                    change_type="added",
                    new_value=new_field
                ))
                
        return changes
        
    async def create_initial_version(self, schema: FormSchema) -> VersionedFormSchema:
        """Create the first version of a form schema"""
        versioned_schema = VersionedFormSchema(
            **schema.dict(),
            schema_version=SchemaVersion(major=1, minor=0, patch=0),
            compatibility=["1.0.0"]
        )
        
        try:
            result = await self.collection.insert_one(versioned_schema.dict())
            versioned_schema.id = str(result.inserted_id)
            return versioned_schema
        except DuplicateKeyError:
            raise ValueError(f"Schema version already exists for form type {schema.form_type}")
            
    async def get_latest_version(self, form_type: str) -> Optional[Dict[str, Any]]:
        """Get the latest version of a form schema"""
        result = await self.collection.find_one(
            {"form_type": form_type},
            sort=[
                ("schema_version.major", -1),
                ("schema_version.minor", -1),
                ("schema_version.patch", -1)
            ]
        )
        
        if not result:
            return None
            
        # Ensure version field is set
        if "version" not in result:
            version = result["schema_version"]
            result["version"] = f"{version['major']}.{version['minor']}.{version['patch']}"
            
        return result
        
    async def get_version(self, form_type: str, version: str) -> Optional[Dict[str, Any]]:
        """Get a specific version of a form schema"""
        major, minor, patch = map(int, version.split("."))
        result = await self.collection.find_one({
            "form_type": form_type,
            "schema_version.major": major,
            "schema_version.minor": minor,
            "schema_version.patch": patch
        })
        
        if not result and "version" not in result:
            version = result["schema_version"]
            result["version"] = f"{version['major']}.{version['minor']}.{version['patch']}"
            
        return result
        
    async def create_new_version(
        self,
        form_type: str,
        new_schema: FormSchema,
        breaking_changes: bool = False,
        migration_notes: Optional[str] = None
    ) -> VersionedFormSchema:
        """Create a new version of an existing form schema"""
        current = await self.get_latest_version(form_type)
        if not current:
            return await self.create_initial_version(new_schema)
            
        # Calculate version changes
        changes = self._calculate_field_changes(current, new_schema)
        new_version = self._get_next_version(current.schema_version, breaking_changes)
        
        # Create version diff
        version_diff = VersionDiff(
            from_version=str(current.schema_version),
            to_version=str(new_version),
            changes=changes,
            migration_notes=migration_notes,
            breaking_changes=breaking_changes
        )
        
        # Create new versioned schema
        versioned_schema = VersionedFormSchema(
            **new_schema.dict(),
            schema_version=new_version,
            previous_version=str(current.schema_version),
            version_changes=version_diff,
            compatibility=[str(new_version)],
            migration_strategy="in-place" if not breaking_changes else "manual"
        )
        
        # Update previous version's next_version reference
        await self.collection.update_one(
            {"form_type": form_type, "schema_version": current.schema_version.dict()},
            {"$set": {"next_version": str(new_version)}}
        )
        
        # Insert new version
        try:
            result = await self.collection.insert_one(versioned_schema.dict())
            versioned_schema.id = str(result.inserted_id)
            return versioned_schema
        except DuplicateKeyError:
            raise ValueError(f"Version {new_version} already exists for form type {form_type}")
            
    async def list_versions(self, form_type: str) -> List[Dict[str, Any]]:
        """List all versions of a form schema with basic metadata"""
        cursor = self.collection.find(
            {"form_type": form_type},
            projection={
                "schema_version": 1,
                "created_at": 1,
                "total_fields": 1,
                "breaking_changes": 1
            }
        ).sort("schema_version.released", -1)
        
        return [doc async for doc in cursor]
        
    async def deprecate_version(self, form_type: str, version: str) -> bool:
        """Mark a schema version as deprecated"""
        major, minor, patch = map(int, version.split("."))
        result = await self.collection.update_one(
            {
                "form_type": form_type,
                "schema_version.major": major,
                "schema_version.minor": minor,
                "schema_version.patch": patch
            },
            {"$set": {"schema_version.deprecated": True}}
        )
        return result.modified_count > 0
        
    async def find_compatible_version(self, form_type: str, target_version: str) -> Optional[str]:
        """Find the most recent version compatible with the target version"""
        result = await self.collection.find_one(
            {
                "form_type": form_type,
                "compatibility": target_version,
                "schema_version.deprecated": {"$ne": True}
            },
            sort=[("schema_version.released", -1)]
        )
        return str(result["schema_version"]) if result else None

    async def create_schema(self, form_type: str, fields: List[Dict[str, Any]], draft: bool = True) -> Dict[str, Any]:
        """Create a new schema version for a form type"""
        # Get the latest version for this form type
        latest = await self._get_latest_version(form_type)
        
        # Calculate new version
        if latest:
            version = {
                "major": latest["schema_version"]["major"],
                "minor": latest["schema_version"]["minor"] + 1,
                "patch": 0,
                "released": DRAFT_DATE if draft else datetime.now(UTC)
            }
        else:
            # First version
            version = {
                "major": 1,
                "minor": 0,
                "patch": 0,
                "released": DRAFT_DATE if draft else datetime.now(UTC)
            }
        
        # Create new schema document
        schema = {
            "form_type": form_type,
            "version": f"{version['major']}.{version['minor']}.{version['patch']}",
            "schema_version": version,
            "fields": fields,
            "total_fields": len(fields),
            "created_at": datetime.now(UTC),
            "metadata": {
                "draft": draft,
                "created_by": "system"  # TODO: Add user context
            }
        }
        
        # Insert and return the new schema
        result = await self.collection.insert_one(schema)
        schema["_id"] = result.inserted_id
        return schema
    
    async def get_schema(self, form_type: str, version: Optional[Dict[str, int]] = None) -> Optional[Dict[str, Any]]:
        """Get a specific schema version or the latest released version"""
        if version:
            # Get specific version
            query = {
                "form_type": form_type,
                "schema_version.major": version.get("major"),
                "schema_version.minor": version.get("minor", 0),
                "schema_version.patch": version.get("patch", 0)
            }
        else:
            # Get latest released version
            query = {
                "form_type": form_type,
                "schema_version.released": {"$lt": DRAFT_DATE}  # Only get actually released versions
            }
            
        result = await self.collection.find_one(
            query,
            sort=[("schema_version.major", -1), 
                  ("schema_version.minor", -1),
                  ("schema_version.patch", -1)]
        )
        return result
    
    async def list_schemas(self, form_type: str, include_drafts: bool = False) -> List[Dict[str, Any]]:
        """List all schema versions for a form type"""
        query = {"form_type": form_type}
        if not include_drafts:
            query["schema_version.released"] = {"$lt": DRAFT_DATE}
            
        cursor = self.collection.find(
            query,
            sort=[("schema_version.major", -1),
                  ("schema_version.minor", -1),
                  ("schema_version.patch", -1)]
        )
        
        return [doc async for doc in cursor]
    
    async def release_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """Release a draft schema version"""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(schema_id), "schema_version.released": DRAFT_DATE},
            {"$set": {
                "schema_version.released": datetime.now(UTC),
                "metadata.draft": False
            }},
            return_document=True
        )
        return result
    
    async def update_schema_fields(self, schema_id: str, fields: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Update fields in a draft schema version"""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(schema_id), "schema_version.released": DRAFT_DATE},
            {"$set": {
                "fields": fields,
                "total_fields": len(fields)
            }},
            return_document=True
        )
        return result
    
    async def delete_draft_schema(self, schema_id: str) -> bool:
        """Delete a draft schema version"""
        result = await self.collection.delete_one({
            "_id": ObjectId(schema_id),
            "schema_version.released": DRAFT_DATE
        })
        return result.deleted_count > 0
    
    async def _get_latest_version(self, form_type: str) -> Optional[Dict[str, Any]]:
        """Get the latest version (including drafts) for a form type"""
        return await self.collection.find_one(
            {"form_type": form_type},
            sort=[("schema_version.major", -1),
                  ("schema_version.minor", -1),
                  ("schema_version.patch", -1)]
        ) 