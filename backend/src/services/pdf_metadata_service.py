"""PDF metadata service"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from PyPDF2 import PdfReader
from PyPDF2.generic import NameObject
from bson import ObjectId
from src.db.database import Database
from src.services.pdf_storage_service import PDFStorageService
from src.services.cache_service import CacheService
import logging
from pymongo import ASCENDING, DESCENDING
from models.form_schema import FormSchema, FormFieldDefinition
from pydantic import BaseModel, Field

class PDFMetadataService:
    """Service for extracting and managing PDF form metadata"""
    
    def __init__(self):
        database = Database()
        self.db = database.db
        self.storage_service = PDFStorageService()
        self.cache_service = CacheService()
        self.forms_collection = self.db['forms']
        self.logger = logging.getLogger(__name__)
        
        # Projection to exclude large field data when not needed
        self.metadata_projection = {
            'fields': 0
        }
        
        # Cache keys
        self.FORM_LIST_KEY = "form_list:{form_type}:page{page}:limit{limit}"
        self.FORM_METADATA_KEY = "form_metadata:{form_id}"
        self.FORM_FIELDS_KEY = "form_fields:{form_id}"
    
    async def extract_metadata(self, pdf_path: str, form_type: str) -> Dict[str, Any]:
        """Extract metadata and field definitions from a PDF form"""
        try:
            reader = PdfReader(pdf_path)
            
            # Get form fields
            if not reader.get_form_text_fields() and not reader.get_fields():
                raise ValueError("No form fields found in PDF")
            
            # Extract basic metadata
            metadata = {
                'id': str(ObjectId()),
                'title': form_type.upper(),
                'description': f'Form {form_type.upper()} field definitions',
                'pages': len(reader.pages),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'form_type': form_type,
                'fields': []
            }
            
            # Extract field definitions with detailed metadata
            pdf_fields = reader.get_fields()
            for field_name, field in pdf_fields.items():
                field_def = self._extract_field_metadata(field_name, field)
                if field_def:  # Only add if we got valid metadata
                    metadata['fields'].append(field_def)
            
            # Store in MongoDB
            await self.forms_collection.insert_one(metadata)
            
            # Cache the metadata without fields for list operations
            list_metadata = {**metadata}
            del list_metadata['fields']
            await self.cache_service.set(
                f"form:metadata:{metadata['id']}",
                list_metadata,
                ttl=self.cache_service.FORM_METADATA_TTL
            )
            
            # Cache the fields separately
            await self.cache_service.set(
                f"form:fields:{metadata['id']}",
                metadata['fields'],
                ttl=self.cache_service.FIELD_DEFS_TTL
            )
            
            return metadata
        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {str(e)}")
            raise Exception(f"Failed to extract metadata: {str(e)}")
    
    async def get_form_metadata(self, form_id: str, include_fields: bool = False) -> Optional[Dict[str, Any]]:
        """Get form metadata by ID"""
        try:
            # Try to get metadata from cache first
            cache_key = self.FORM_METADATA_KEY.format(form_id=form_id)
            metadata = await self.cache_service.get(cache_key)
            
            if not metadata:
                # Get from database with appropriate projection
                projection = None if include_fields else self.metadata_projection
                metadata = await self.forms_collection.find_one(
                    {'id': form_id},
                    projection
                )
                
                if metadata:
                    # Cache the metadata
                    await self.cache_service.set(
                        cache_key,
                        metadata,
                        ttl=self.cache_service.FORM_METADATA_TTL
                    )
            
            if metadata and include_fields:
                # Get fields from cache or database
                fields = await self.get_form_fields(form_id)
                if fields:
                    metadata['fields'] = fields
            
            return metadata
        except Exception as e:
            self.logger.error(f"Failed to get form metadata: {str(e)}")
            raise Exception(f"Failed to get form metadata: {str(e)}")
    
    async def list_forms(
        self,
        form_type: str,
        page: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """List forms with pagination and caching"""
        cache_key = self.FORM_LIST_KEY.format(
            form_type=form_type,
            page=page,
            limit=limit
        )
        
        # Try cache first
        cached_forms = await self.cache_service.get(cache_key)
        if cached_forms is not None:
            return cached_forms
        
        # Cache miss, query database
        skip = (page - 1) * limit
        cursor = self.forms_collection.find(
            {"form_type": form_type},
            sort=[("created_at", DESCENDING)]
        ).skip(skip).limit(limit)
        
        forms = await cursor.to_list(length=limit)
        
        # Cache the results
        await self.cache_service.set(cache_key, forms)
        
        return forms
    
    async def get_form_fields(
        self,
        form_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get form fields with caching"""
        cache_key = self.FORM_FIELDS_KEY.format(form_id=form_id)
        
        # Try cache first
        cached_fields = await self.cache_service.get(cache_key)
        if cached_fields is not None:
            return cached_fields
        
        # Cache miss, query database
        form = await self.forms_collection.find_one(
            {"id": form_id},
            projection={"fields": 1}
        )
        
        if form is None:
            return None
        
        fields = form.get("fields", [])
        
        # Cache the results
        await self.cache_service.set(cache_key, fields)
        
        return fields
    
    async def update_field_definitions(
        self,
        form_id: str,
        fields: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Update field definitions for a form"""
        try:
            # Validate field IDs are unique
            field_ids = [f['field_id'] for f in fields]
            if len(field_ids) != len(set(field_ids)):
                raise ValueError("Duplicate field IDs found")
            
            update_result = await self.forms_collection.update_one(
                {'id': form_id},
                {
                    '$set': {
                        'fields': fields,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if update_result.modified_count > 0:
                # Clear all related cache entries
                await self.cache_service.clear_form_cache(form_id)
                
                # Return updated form with fresh cache
                return await self.get_form_metadata(form_id, include_fields=True)
            
            return None
        except Exception as e:
            self.logger.error(f"Failed to update field definitions: {str(e)}")
            raise Exception(f"Failed to update field definitions: {str(e)}")
    
    async def delete_form_metadata(self, form_id: str) -> bool:
        """Delete form metadata from the database"""
        try:
            result = await self.forms_collection.delete_one({'id': form_id})
            
            # Clear all related cache entries
            if result.deleted_count > 0:
                await self.cache_service.clear_form_cache(form_id)
            
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Failed to delete form metadata: {str(e)}")
            raise Exception(f"Failed to delete form metadata: {str(e)}")
            
    def _extract_field_metadata(self, field_name: str, field: NameObject) -> Optional[Dict[str, Any]]:
        """Extract metadata for a single form field"""
        try:
            if not isinstance(field, dict):
                return None
                
            return {
                'field_id': field_name,
                'field_type': field.get('/FT', '').decode('utf-8') if isinstance(field.get('/FT'), bytes) else field.get('/FT', ''),
                'field_name': field.get('/T', field_name).decode('utf-8') if isinstance(field.get('/T'), bytes) else field.get('/T', field_name),
                'field_value': field.get('/V', None),
                'position': self._extract_field_position(field),
                'properties': self._extract_field_properties(field),
                'tooltip': field.get('/TU', '').decode('utf-8') if isinstance(field.get('/TU'), bytes) else field.get('/TU', ''),
                'label': field.get('/TM', '').decode('utf-8') if isinstance(field.get('/TM'), bytes) else field.get('/TM', '')
            }
        except Exception as e:
            self.logger.warning(f"Failed to extract metadata for field {field_name}: {str(e)}")
            return None
    
    def _extract_field_position(self, field: Dict) -> Dict:
        """Extract field position information"""
        try:
            rect = field.get('/Rect', [0, 0, 0, 0])
            if hasattr(rect, 'get_object'):
                rect = rect.get_object()
            return {
                'x': rect[0],
                'y': rect[1],
                'width': rect[2] - rect[0],
                'height': rect[3] - rect[1]
            }
        except:
            return {'x': 0, 'y': 0, 'width': 0, 'height': 0}
    
    def _extract_field_properties(self, field: Dict) -> Dict:
        """Extract all other properties for a single form field"""
        try:
            properties = {}
            for key in field:
                if key.startswith('/'):
                    value = field[key]
                    if hasattr(value, 'get_object'):
                        value = value.get_object()
                    clean_key = key[1:]  # Remove leading slash
                    properties[clean_key] = str(value)
            return properties
        except Exception as e:
            self.logger.warning(f"Error extracting field properties: {str(e)}")
            return {}
    
    async def update_form_fields(
        self,
        form_id: str,
        fields: List[Dict[str, Any]]
    ) -> bool:
        """Update form fields and invalidate cache"""
        result = await self.forms_collection.update_one(
            {"id": form_id},
            {"$set": {"fields": fields}}
        )
        
        if result.modified_count > 0:
            # Invalidate caches
            await self.cache_service.delete(self.FORM_METADATA_KEY.format(form_id=form_id))
            await self.cache_service.delete(self.FORM_FIELDS_KEY.format(form_id=form_id))
            return True
        
        return False
    
    async def delete_form(self, form_id: str) -> bool:
        """Delete form and invalidate cache"""
        result = await self.forms_collection.delete_one({"id": form_id})
        
        if result.deleted_count > 0:
            # Invalidate caches
            await self.cache_service.delete(self.FORM_METADATA_KEY.format(form_id=form_id))
            await self.cache_service.delete(self.FORM_FIELDS_KEY.format(form_id=form_id))
            return True
        
        return False 