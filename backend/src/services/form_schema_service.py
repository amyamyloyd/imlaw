"""Form Schema Service

This service handles loading and managing form schemas and field mappings.
It provides functionality to:
1. Load form schemas from JSON files
2. Map source fields to PDF field IDs
3. Handle repeatable sections like addresses
"""
from typing import Dict, Any, List, Optional
import json
import os
import logging
from datetime import datetime
from ..models.form_schema import FormSchema, FormFieldDefinition, FieldType, Position
from ..models.repeatable_section import RepeatableSection, FieldMapping
from ..utils.form_mapping_converter import convert_mapping_to_schema

logger = logging.getLogger(__name__)

class FormSchemaService:
    """Service for managing form schemas and field mappings."""
    
    def __init__(self):
        """Initialize the Form Schema Service."""
        self.logger = logging.getLogger(__name__)
        # Get the root directory (one level up from backend)
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.scripts_dir = os.path.join(self.root_dir, '..', 'generalscripts')
        
        # Cache for loaded schemas
        self._schema_cache: Dict[str, FormSchema] = {}
        
    def _load_field_names(self, form_type: str) -> Dict[str, Any]:
        """Load field names from the JSON file."""
        # Remove any hyphens from form type and convert to lowercase
        filename = f"{form_type.lower().replace('-', '')}_fields.json"
        filepath = os.path.join(self.scripts_dir, filename)
        
        if not os.path.exists(filepath):
            raise ValueError(f"Field names file not found: {filename}")
            
        with open(filepath, 'r') as f:
            return json.load(f)
            
    def _load_field_mappings(self, form_type: str) -> List[Dict[str, Any]]:
        """Load field mappings from the JSON file."""
        # Remove any hyphens from form type and convert to lowercase
        filename = f"{form_type.lower().replace('-', '')}_fill_map.json"
        filepath = os.path.join(self.scripts_dir, filename)
        
        if not os.path.exists(filepath):
            raise ValueError(f"Field mappings file not found: {filename}")
            
        with open(filepath, 'r') as f:
            return json.load(f)
            
    def get_form_schema(self, form_type: str, refresh: bool = False) -> FormSchema:
        """
        Get the form schema for a specific form type.
        Uses cached version unless refresh is True.
        
        Args:
            form_type: The type of form (e.g., 'I-485')
            refresh: Whether to force reload the schema from files
            
        Returns:
            FormSchema: The form schema with field definitions and mappings
            
        Raises:
            ValueError: If schema files are not found or invalid
        """
        # Check cache first unless refresh requested
        cache_key = form_type.upper()
        if not refresh and cache_key in self._schema_cache:
            return self._schema_cache[cache_key]
            
        try:
            # Load field names and mappings
            field_names = self._load_field_names(form_type)
            field_mappings = self._load_field_mappings(form_type)
            
            # Convert mappings to schema
            schema = convert_mapping_to_schema(field_mappings)
            
            # Add repeatable sections for addresses
            address_fields = {
                "street_number_name": "StreetNumberName",
                "apt_ste_flr": "AptSteFlrNumber",
                "city_or_town": "CityOrTown",
                "state": "State",
                "zip_code": "ZipCode",
                "province": "Province",
                "postal_code": "PostalCode",
                "country": "Country"
            }
            
            # Create address section mappings
            address_mappings = {}
            for field_name, pdf_suffix in address_fields.items():
                field_indices = []
                # Look for fields like Pt3Line5_StreetNumberName[0], Pt3Line7_StreetNumberName[0], etc.
                for pdf_field_id in field_names.keys():
                    if f"_{pdf_suffix}[0]" in pdf_field_id:
                        # Extract the line number (e.g., 5 from Pt3Line5)
                        if "Line" in pdf_field_id:
                            line_num = int(pdf_field_id.split("Line")[1].split("_")[0])
                            field_indices.append(line_num)
                
                if field_indices:
                    # Sort indices to ensure consistent order
                    field_indices.sort()
                    # Create field mapping with pattern using the first field as template
                    template_field = next(k for k in field_names.keys() if f"_{pdf_suffix}[0]" in k)
                    pattern_parts = template_field.split("Line")
                    pattern = f"{pattern_parts[0]}Line{{index}}_{pdf_suffix}[0]"
                    
                    address_mappings[field_name] = FieldMapping(
                        field_name=field_name,
                        pdf_field_pattern=pattern,
                        field_indices=field_indices
                    )
            
            # Add address section to schema if mappings found
            if address_mappings:
                schema.repeatable_sections["addresses"] = RepeatableSection(
                    section_name="addresses",
                    field_mappings=address_mappings,
                    max_entries_per_page=len(field_indices)
                )
            
            # Cache the schema
            self._schema_cache[cache_key] = schema
            return schema
            
        except Exception as e:
            self.logger.error(f"Error loading form schema: {str(e)}")
            raise 