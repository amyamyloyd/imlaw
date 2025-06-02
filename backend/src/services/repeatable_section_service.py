"""Repeatable Section Service.

This service handles operations for repeatable sections within client profiles, including:
- Adding/removing sections
- Updating section data
- Reordering sections
- Section validation and completion tracking

The service uses MongoDB's array operators for efficient updates.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from bson import ObjectId
from src.db.database import Database
from src.models.client_profile import (
    ClientProfile,
    RepeatableSection,
    Address,
    Employment,
    Education,
    FamilyMember
)
import os
from PyPDF2 import PdfReader, PdfWriter

from src.models.repeatable_section import RepeatableFieldMapping
from src.services.pdf_storage_service import PDFStorageService

class RepeatableSectionService:
    """Service for managing repeatable sections in client profiles."""
    
    def __init__(self):
        """Initialize service with MongoDB connection."""
        database = Database()
        self.db = database.db
        self.clients_collection = self.db['client_profiles']
        
        # Map section types to their corresponding array fields in ClientProfile
        self.section_field_map = {
            'address': 'addresses',
            'employment': 'employment',
            'education': 'education',
            'family': 'family_members'
        }
        
        # Map section types to their model classes
        self.section_class_map = {
            'address': Address,
            'employment': Employment,
            'education': Education,
            'family': FamilyMember
        }
        
        self.storage_service = PDFStorageService()
    
    async def add_section(
        self,
        client_id: str,
        section_type: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Add a new repeatable section to a client profile.
        
        Args:
            client_id: ID of the client profile
            section_type: Type of section to add
            data: Section-specific data
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
            
        Example:
            success, error = await service.add_section(
                "client123",
                "address",
                {"street": "123 Main St", "city": "Boston"}
            )
        """
        if section_type not in self.section_field_map:
            return False, f"Invalid section type: {section_type}"
            
        array_field = self.section_field_map[section_type]
        section_class = self.section_class_map[section_type]
        
        try:
            # Get current count for order
            result = await self.clients_collection.find_one(
                {"client_id": client_id},
                {array_field: 1}
            )
            if not result:
                return False, "Client not found"
                
            current_sections = result.get(array_field, [])
            
            # Create new section
            new_section = section_class(
                order=len(current_sections),
                data=data
            )
            
            # Add to array
            update_result = await self.clients_collection.update_one(
                {"client_id": client_id},
                {
                    "$push": {array_field: new_section.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            return update_result.modified_count > 0, None
            
        except Exception as e:
            return False, str(e)
    
    async def update_section(
        self,
        client_id: str,
        section_type: str,
        section_index: int,
        data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Update data in a specific repeatable section.
        
        Args:
            client_id: ID of the client profile
            section_type: Type of section to update
            section_index: Index of the section in its array
            data: Updated section data
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
            
        Example:
            success, error = await service.update_section(
                "client123",
                "address",
                0,
                {"street": "456 Oak St"}
            )
        """
        if section_type not in self.section_field_map:
            return False, f"Invalid section type: {section_type}"
            
        array_field = self.section_field_map[section_type]
        
        try:
            # Update specific array element
            update_result = await self.clients_collection.update_one(
                {"client_id": client_id},
                {
                    "$set": {
                        f"{array_field}.{section_index}.data": data,
                        f"{array_field}.{section_index}.updated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return update_result.modified_count > 0, None
            
        except Exception as e:
            return False, str(e)
    
    async def remove_section(
        self,
        client_id: str,
        section_type: str,
        section_index: int
    ) -> Tuple[bool, Optional[str]]:
        """Remove a repeatable section from a client profile.
        
        Args:
            client_id: ID of the client profile
            section_type: Type of section to remove
            section_index: Index of the section to remove
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
            
        Example:
            success, error = await service.remove_section(
                "client123",
                "address",
                0
            )
        """
        if section_type not in self.section_field_map:
            return False, f"Invalid section type: {section_type}"
            
        array_field = self.section_field_map[section_type]
        
        try:
            # Remove array element and reorder remaining elements
            update_result = await self.clients_collection.update_one(
                {"client_id": client_id},
                {
                    "$pull": {
                        array_field: {"order": section_index}
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if update_result.modified_count > 0:
                # Update order of remaining elements
                await self._reorder_sections(client_id, section_type)
                return True, None
            
            return False, "Section not found"
            
        except Exception as e:
            return False, str(e)
    
    async def reorder_sections(
        self,
        client_id: str,
        section_type: str,
        new_order: List[int]
    ) -> Tuple[bool, Optional[str]]:
        """Reorder sections of a specific type.
        
        Args:
            client_id: ID of the client profile
            section_type: Type of sections to reorder
            new_order: List of current indices in their new order
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
            
        Example:
            success, error = await service.reorder_sections(
                "client123",
                "address",
                [2, 0, 1]  # Move third address to first position
            )
        """
        if section_type not in self.section_field_map:
            return False, f"Invalid section type: {section_type}"
            
        array_field = self.section_field_map[section_type]
        
        try:
            # Get current sections
            result = await self.clients_collection.find_one(
                {"client_id": client_id},
                {array_field: 1}
            )
            if not result:
                return False, "Client not found"
                
            current_sections = result.get(array_field, [])
            if len(new_order) != len(current_sections):
                return False, "Invalid order list length"
                
            # Update order for each section
            for new_idx, old_idx in enumerate(new_order):
                if old_idx >= len(current_sections):
                    return False, f"Invalid index in order list: {old_idx}"
                    
                await self.clients_collection.update_one(
                    {"client_id": client_id},
                    {
                        "$set": {
                            f"{array_field}.{old_idx}.order": new_idx,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    async def _reorder_sections(
        self,
        client_id: str,
        section_type: str
    ) -> None:
        """Update order values after removing a section.
        
        Args:
            client_id: ID of the client profile
            section_type: Type of sections to reorder
        """
        array_field = self.section_field_map[section_type]
        
        # Get current sections
        result = await self.clients_collection.find_one(
            {"client_id": client_id},
            {array_field: 1}
        )
        if not result:
            return
            
        sections = result.get(array_field, [])
        
        # Update order for each section
        for i, section in enumerate(sections):
            await self.clients_collection.update_one(
                {"client_id": client_id},
                {
                    "$set": {
                        f"{array_field}.{i}.order": i
                    }
                }
            )
    
    async def mark_section_complete(
        self,
        client_id: str,
        section_type: str,
        section_index: int,
        is_complete: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Mark a section as complete or incomplete.
        
        Args:
            client_id: ID of the client profile
            section_type: Type of section to update
            section_index: Index of the section
            is_complete: Whether the section is complete
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
            
        Example:
            success, error = await service.mark_section_complete(
                "client123",
                "address",
                0,
                True
            )
        """
        if section_type not in self.section_field_map:
            return False, f"Invalid section type: {section_type}"
            
        array_field = self.section_field_map[section_type]
        
        try:
            update_result = await self.clients_collection.update_one(
                {"client_id": client_id},
                {
                    "$set": {
                        f"{array_field}.{section_index}.is_complete": is_complete,
                        f"{array_field}.{section_index}.updated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if update_result.modified_count > 0:
                # Update completion status in save_progress
                await self._update_section_completion(client_id, section_type)
                return True, None
            
            return False, "Section not found"
            
        except Exception as e:
            return False, str(e)
    
    async def _update_section_completion(
        self,
        client_id: str,
        section_type: str
    ) -> None:
        """Update save_progress completion tracking for a section type.
        
        Args:
            client_id: ID of the client profile
            section_type: Type of sections to check
        """
        array_field = self.section_field_map[section_type]
        
        # Get current sections
        result = await self.clients_collection.find_one(
            {"client_id": client_id},
            {array_field: 1, "save_progress": 1}
        )
        if not result:
            return
            
        sections = result.get(array_field, [])
        save_progress = result.get("save_progress", {})
        completed_sections = save_progress.get("completed_sections", [])
        
        # Check if all sections are complete
        all_complete = all(section.get("is_complete", False) for section in sections)
        
        if all_complete and section_type not in completed_sections:
            # Add to completed sections
            await self.clients_collection.update_one(
                {"client_id": client_id},
                {
                    "$addToSet": {
                        "save_progress.completed_sections": section_type
                    }
                }
            )
        elif not all_complete and section_type in completed_sections:
            # Remove from completed sections
            await self.clients_collection.update_one(
                {"client_id": client_id},
                {
                    "$pull": {
                        "save_progress.completed_sections": section_type
                    }
                }
            )
    
    def process_repeatable_section(
        self,
        section: RepeatableSection,
        data_entries: List[Dict[str, Any]],
        writer: PdfWriter,
        base_pdf_path: str
    ) -> Dict[str, Any]:
        """Process a repeatable section and return field mappings for the PDF writer
        
        Args:
            section: RepeatableSection definition
            data_entries: List of data entries for the section
            writer: PDF writer instance
            base_pdf_path: Path to the base PDF file
            
        Returns:
            Dict mapping PDF field IDs to values
        """
        field_mappings = {}
        total_entries = len(data_entries)
        
        # Process entries that fit on the base page
        for idx, entry in enumerate(data_entries):
            if idx >= section.max_entries_per_page:
                break
                
            for field_name, field_mapping in section.field_mappings.items():
                if field_name in entry:
                    # Get the actual field index from field_indices if available
                    if field_mapping.field_indices and idx < len(field_mapping.field_indices):
                        actual_index = field_mapping.field_indices[idx]
                    else:
                        actual_index = idx + 1  # Default to 1-based indexing
                    
                    # Format the field ID using the index
                    field_id = field_mapping.pdf_field_pattern.format(index=actual_index)
                    print(f"Writing {entry[field_name]} to field {field_id}")  # Debug logging
                    field_mappings[field_id] = str(entry[field_name])
        
        return field_mappings