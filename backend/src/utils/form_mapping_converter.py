"""Utility functions for converting form mappings to FormSchema format."""
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from ..models.form_schema import FormSchema, FormFieldDefinition, FieldType, Position

def convert_mapping_to_schema(mapping_data: List[Dict[str, Any]]) -> FormSchema:
    """
    Convert mapping data from i485_fill_map.json to FormSchema.
    
    Args:
        mapping_data: List of field mapping dictionaries
        
    Returns:
        FormSchema instance
    """
    fields = []
    
    # Group fields by source field name
    source_field_groups = defaultdict(list)
    for field_map in mapping_data:
        source_field = field_map.get("source_i485_field_original")
        if source_field:
            source_field_groups[source_field].append(field_map)
    
    # Create field definitions
    for source_field, field_maps in source_field_groups.items():
        # Create a field definition for each PDF field that maps to this source field
        for field_map in field_maps:
            field_id = field_map["pdf_internal_id"]
            field_label = field_map["pdf_field_label_original"]
            
            # For now, all fields are simple text fields
            field_type = FieldType.TEXT
            
            # Create field definition that maps source field to PDF field
            field = FormFieldDefinition(
                field_id=field_id,  # The PDF's internal field ID
                field_type=field_type,
                field_name=source_field,  # The standardized source field name
                label=field_label,
                position=Position(x=0, y=0, width=100, height=20),  # Default position
                page_number=1,  # Default to page 1
                required=True,  # Default to required
                validation_rules=[],  # No validation rules by default
                options=[],  # No options by default
                metadata={
                    "source_label": field_map.get("source_i485_label", ""),
                    "jira_fields": field_map.get("jira_source_fields", [])
                }
            )
            fields.append(field)
    
    # Create form schema
    schema = FormSchema(
        form_type="I-485",
        version="2023",
        title="Application to Register Permanent Residence or Adjust Status",
        fields=fields,
        total_fields=len(fields),
        metadata={
            "source": "i485_fill_map.json",
            "conversion_date": datetime.utcnow().isoformat(),
            "field_groups": {
                source_field: [f["pdf_internal_id"] for f in maps]
                for source_field, maps in source_field_groups.items()
            }
        },
        repeatable_sections={}  # No repeatable sections for now
    )
    
    return schema 