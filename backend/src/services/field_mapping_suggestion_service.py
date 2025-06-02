"""Field mapping suggestion service"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
from difflib import SequenceMatcher
from collections import defaultdict
from bson import ObjectId
from pymongo.database import Database
from src.models.canonical_field import CanonicalField, FormFieldMapping
from src.services.canonical_field_service import CanonicalFieldService
from src.services.field_transform_service import FieldTransformService, TransformRule, TransformType

class FieldMappingSuggestionService:
    """Service for suggesting field mappings based on field names and metadata"""
    
    def __init__(self):
        self.canonical_service = CanonicalFieldService()
        self.transform_service = FieldTransformService()
        
        # Common field name patterns
        self.name_patterns = {
            "given_name": [
                r"(?:given|first)[-_]?name",
                r"name[-_]?(?:given|first)",
                r"first",
                r"givenname"
            ],
            "family_name": [
                r"(?:family|last|sur)[-_]?name",
                r"name[-_]?(?:family|last|sur)",
                r"surname",
                r"lastname"
            ],
            "birth_date": [
                r"(?:birth|dob)[-_]?date",
                r"date[-_]?(?:of)?[-_]?birth",
                r"dob",
                r"birthdate"
            ],
            "email": [
                r"e?[-_]?mail[-_]?(?:address)?",
                r"electronic[-_]?mail"
            ],
            "phone": [
                r"(?:phone|telephone|mobile|cell)[-_]?(?:number)?",
                r"contact[-_]?number"
            ]
        }
        
        # Common field value patterns
        self.value_patterns = {
            "date": [
                r"^\d{2}[-/]\d{2}[-/]\d{4}$",  # mm/dd/yyyy or mm-dd-yyyy
                r"^\d{4}[-/]\d{2}[-/]\d{2}$",  # yyyy/mm/dd or yyyy-mm-dd
                r"^\d{8}$"  # mmddyyyy
            ],
            "email": [
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            ],
            "phone": [
                r"^\+?1?\d{10}$",  # +1XXXXXXXXXX or XXXXXXXXXX
                r"^\d{3}[-.]?\d{3}[-.]?\d{4}$"  # XXX-XXX-XXXX or XXX.XXX.XXXX
            ],
            "boolean": [
                r"^(?:yes|no|true|false|1|0|y|n|t|f)$"
            ],
            "number": [
                r"^-?\d+\.?\d*$"
            ]
        }
    
    async def suggest_mappings(
        self,
        form_fields: List[Dict[str, Any]],
        form_type: str,
        form_version: str,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Suggest canonical field mappings for form fields"""
        suggestions = []
        
        # Get all canonical fields for reference
        canonical_fields = await self.canonical_service.get_fields(include_inactive=False)
        
        for field in form_fields:
            field_id = field.get("field_id")
            if not field_id:
                continue
                
            # Get field properties
            field_label = field.get("label", "").lower()
            field_desc = field.get("description", "").lower()
            field_value = field.get("value")
            field_type = field.get("type", "string")
            
            # Find best matching canonical field
            best_match = await self._find_best_match(
                field_id=field_id,
                field_label=field_label,
                field_desc=field_desc,
                field_value=field_value,
                field_type=field_type,
                canonical_fields=canonical_fields
            )
            
            if best_match and best_match["confidence"] >= min_confidence:
                # Create transform rule if needed
                transform_rule = None
                if best_match["canonical_field"].data_type != field_type:
                    transform_rule = self.transform_service.create_transform_rule(
                        source_value=field_value,
                        target_schema={"type": best_match["canonical_field"].data_type}
                    )
                
                suggestions.append({
                    "form_field": field,
                    "canonical_field": best_match["canonical_field"],
                    "confidence": best_match["confidence"],
                    "transform_rule": transform_rule,
                    "reason": best_match["reason"]
                })
        
        return suggestions
    
    async def _find_best_match(
        self,
        field_id: str,
        field_label: str,
        field_desc: str,
        field_value: Any,
        field_type: str,
        canonical_fields: List[CanonicalField]
    ) -> Optional[Dict[str, Any]]:
        """Find the best matching canonical field"""
        best_match = None
        best_confidence = 0
        best_reason = ""
        
        # Normalize field identifiers
        norm_field_id = self._normalize_field_name(field_id)
        norm_label = self._normalize_field_name(field_label)
        
        for canonical_field in canonical_fields:
            # Calculate match scores
            name_score = self._calculate_name_match(
                norm_field_id,
                norm_label,
                canonical_field
            )
            
            pattern_score = self._calculate_pattern_match(
                norm_field_id,
                norm_label,
                canonical_field
            )
            
            value_score = self._calculate_value_match(
                field_value,
                field_type,
                canonical_field
            )
            
            # Weight the scores
            confidence = (
                name_score * 0.5 +  # Field name is most important
                pattern_score * 0.3 +  # Known patterns are good indicators
                value_score * 0.2  # Value format provides additional confidence
            )
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = canonical_field
                best_reason = self._generate_match_reason(
                    name_score,
                    pattern_score,
                    value_score,
                    canonical_field
                )
        
        if best_match:
            return {
                "canonical_field": best_match,
                "confidence": best_confidence,
                "reason": best_reason
            }
        
        return None
    
    def _normalize_field_name(self, name: str) -> str:
        """Normalize a field name for comparison"""
        if not name:
            return ""
        
        # Convert to lowercase
        name = name.lower()
        
        # Remove common prefixes/suffixes
        name = re.sub(r"^(?:field_|frm_|txt_|input_)", "", name)
        name = re.sub(r"(?:_field|_input|_txt)$", "", name)
        
        # Replace separators with underscore
        name = re.sub(r"[-\s.]", "_", name)
        
        # Remove duplicate underscores
        name = re.sub(r"_+", "_", name)
        
        # Remove non-alphanumeric characters
        name = re.sub(r"[^a-z0-9_]", "", name)
        
        return name
    
    def _calculate_name_match(
        self,
        norm_field_id: str,
        norm_label: str,
        canonical_field: CanonicalField
    ) -> float:
        """Calculate match score based on field names"""
        # Get normalized canonical names
        canonical_names = [
            self._normalize_field_name(canonical_field.field_name),
            *[self._normalize_field_name(alias) for alias in canonical_field.aliases]
        ]
        
        # Calculate best match score
        best_score = 0
        for canonical_name in canonical_names:
            # Check exact match
            if norm_field_id == canonical_name or norm_label == canonical_name:
                return 1.0
            
            # Calculate similarity scores
            id_score = SequenceMatcher(None, norm_field_id, canonical_name).ratio()
            label_score = SequenceMatcher(None, norm_label, canonical_name).ratio()
            
            # Use the better score
            score = max(id_score, label_score)
            best_score = max(best_score, score)
        
        return best_score
    
    def _calculate_pattern_match(
        self,
        norm_field_id: str,
        norm_label: str,
        canonical_field: CanonicalField
    ) -> float:
        """Calculate match score based on known patterns"""
        # Get patterns for this canonical field type
        patterns = self.name_patterns.get(canonical_field.field_name, [])
        
        # Check if field matches any pattern
        for pattern in patterns:
            if (re.search(pattern, norm_field_id, re.I) or
                re.search(pattern, norm_label, re.I)):
                return 1.0
        
        return 0.0
    
    def _calculate_value_match(
        self,
        value: Any,
        field_type: str,
        canonical_field: CanonicalField
    ) -> float:
        """Calculate match score based on value format"""
        if value is None:
            return 0.0
        
        # Get expected patterns for the canonical field type
        expected_patterns = self.value_patterns.get(canonical_field.data_type, [])
        
        # Check if value matches expected format
        str_value = str(value).lower().strip()
        for pattern in expected_patterns:
            if re.match(pattern, str_value):
                return 1.0
        
        # If types match exactly
        if field_type == canonical_field.data_type:
            return 0.8
        
        # If types are compatible
        compatible_types = {
            "string": ["text", "varchar", "char"],
            "number": ["integer", "float", "decimal"],
            "date": ["datetime", "timestamp"]
        }
        
        if (field_type in compatible_types.get(canonical_field.data_type, []) or
            canonical_field.data_type in compatible_types.get(field_type, [])):
            return 0.6
        
        return 0.0
    
    def _generate_match_reason(
        self,
        name_score: float,
        pattern_score: float,
        value_score: float,
        canonical_field: CanonicalField
    ) -> str:
        """Generate a human-readable reason for the match"""
        reasons = []
        
        if name_score > 0.9:
            reasons.append("Field names match closely")
        elif name_score > 0.7:
            reasons.append("Field names are similar")
        
        if pattern_score > 0:
            reasons.append(f"Matches common pattern for {canonical_field.display_name}")
        
        if value_score > 0.8:
            reasons.append("Value format matches exactly")
        elif value_score > 0.5:
            reasons.append("Value format is compatible")
        
        if not reasons:
            return "Partial match based on combined factors"
        
        return "; ".join(reasons) 