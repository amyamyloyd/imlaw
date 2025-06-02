from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from difflib import SequenceMatcher
from datetime import datetime

from src.models.form_schema import FormSchema, FormFieldDefinition
from src.models.versioned_form_schema import FieldChange, VersionDiff, ChangeType

class SchemaDiffService:
    """Service for calculating differences between form schema versions"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def calculate_diff(self, old_schema: FormSchema, new_schema: FormSchema) -> VersionDiff:
        """Calculate differences between two schema versions"""
        field_changes = self._calculate_field_changes(old_schema.fields, new_schema.fields)
        
        return VersionDiff(
            from_version=old_schema.version,
            to_version=new_schema.version,
            timestamp=datetime.utcnow(),
            changes=field_changes
        )

    def _calculate_field_changes(self, old_fields: List[FormFieldDefinition], 
                               new_fields: List[FormFieldDefinition]) -> List[FieldChange]:
        """Calculate changes between two lists of form fields"""
        changes: List[FieldChange] = []
        old_field_map = {f.field_id: f for f in old_fields}
        new_field_map = {f.field_id: f for f in new_fields}
        
        # Track processed fields to detect removals
        processed_old_fields: Set[str] = set()
        
        # First pass: Find exact matches and modifications
        for new_field_id, new_field in new_field_map.items():
            if new_field_id in old_field_map:
                # Field exists in both versions
                old_field = old_field_map[new_field_id]
                processed_old_fields.add(new_field_id)
                
                # Check for modifications
                field_changes = self._detect_field_changes(old_field, new_field)
                if field_changes:
                    changes.append(FieldChange(
                        field_id=new_field_id,
                        change_type=ChangeType.MODIFIED,
                        previous_value=self._field_to_dict(old_field),
                        new_value=self._field_to_dict(new_field)
                    ))
            else:
                # Check for similar fields that might have been renamed
                similar_old_field = self._find_similar_field(new_field, old_fields)
                if similar_old_field:
                    processed_old_fields.add(similar_old_field.field_id)
                    changes.append(FieldChange(
                        field_id=new_field_id,
                        change_type=ChangeType.MODIFIED,
                        previous_value=self._field_to_dict(similar_old_field),
                        new_value=self._field_to_dict(new_field)
                    ))
                else:
                    # Truly new field
                    changes.append(FieldChange(
                        field_id=new_field_id,
                        change_type=ChangeType.ADDED,
                        previous_value=None,
                        new_value=self._field_to_dict(new_field)
                    ))
        
        # Second pass: Find removed fields
        for old_field_id, old_field in old_field_map.items():
            if old_field_id not in processed_old_fields:
                changes.append(FieldChange(
                    field_id=old_field_id,
                    change_type=ChangeType.REMOVED,
                    previous_value=self._field_to_dict(old_field),
                    new_value=None
                ))
        
        return changes

    def _detect_field_changes(self, old_field: FormFieldDefinition, 
                            new_field: FormFieldDefinition) -> bool:
        """Detect if there are any meaningful changes between two fields"""
        old_dict = self._field_to_dict(old_field)
        new_dict = self._field_to_dict(new_field)
        return old_dict != new_dict

    def _field_to_dict(self, field: FormFieldDefinition) -> Dict[str, Any]:
        """Convert a field to a dictionary for comparison"""
        return {
            "field_type": field.field_type,
            "field_name": field.field_name,
            "flags": field.flags.model_dump(),
            "properties": field.properties,
            "position": field.position.model_dump(),
            "page_number": field.page_number,
            "tooltip": field.tooltip
        }

    def _find_similar_field(self, field: FormFieldDefinition, 
                          old_fields: List[FormFieldDefinition]) -> Optional[FormFieldDefinition]:
        """Find a similar field in the old schema based on name similarity"""
        best_match = None
        highest_score = 0.0
        
        for old_field in old_fields:
            score = SequenceMatcher(None, field.field_name, old_field.field_name).ratio()
            if score > highest_score and score >= self.similarity_threshold:
                highest_score = score
                best_match = old_field
                
        return best_match 