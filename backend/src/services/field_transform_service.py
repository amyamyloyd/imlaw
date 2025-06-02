from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import re
from pydantic import BaseModel, Field
from enum import Enum
import json

class TransformType(str, Enum):
    """Types of field transformations"""
    DIRECT = "direct"  # Direct value copy
    FORMAT = "format"  # Format conversion (e.g., date formats)
    SPLIT = "split"    # Split one field into multiple
    MERGE = "merge"    # Merge multiple fields into one
    MAP = "map"        # Map values (e.g., "Y"/"N" to True/False)
    COMPUTE = "compute"  # Compute value from other fields
    CUSTOM = "custom"  # Custom transformation logic

class TransformRule(BaseModel):
    """Rule for transforming field values"""
    transform_type: TransformType
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the transformation"
    )
    source_fields: List[str] = Field(
        default_factory=list,
        description="Source field IDs for merge/compute operations"
    )
    target_fields: List[str] = Field(
        default_factory=list,
        description="Target field IDs for split operations"
    )
    condition: Optional[str] = Field(
        None,
        description="Optional condition for when to apply the transform"
    )

class FieldTransformService:
    """Service for handling field value transformations"""
    
    def __init__(self):
        # Common date format patterns
        self.date_patterns = {
            "mm/dd/yyyy": r"^\d{2}/\d{2}/\d{4}$",
            "mm-dd-yyyy": r"^\d{2}-\d{2}-\d{4}$",
            "yyyy/mm/dd": r"^\d{4}/\d{2}/\d{2}$",
            "yyyy-mm-dd": r"^\d{4}-\d{2}-\d{2}$",
            "mmddyyyy": r"^\d{8}$"
        }
        
        # Common boolean mappings
        self.bool_mappings = {
            True: ["yes", "y", "true", "t", "1", "x", "✓"],
            False: ["no", "n", "false", "f", "0", ""]
        }
    
    def transform_value(
        self,
        value: Any,
        rule: TransformRule,
        context: Optional[Dict[str, Any]] = None
    ) -> Union[Any, List[Any]]:
        """Transform a value according to the specified rule"""
        if rule.transform_type == TransformType.DIRECT:
            return value
            
        elif rule.transform_type == TransformType.FORMAT:
            return self._apply_format_transform(value, rule.parameters)
            
        elif rule.transform_type == TransformType.SPLIT:
            return self._apply_split_transform(value, rule.parameters)
            
        elif rule.transform_type == TransformType.MERGE:
            if not context or not all(f in context for f in rule.source_fields):
                raise ValueError("Missing required source fields for merge transform")
            return self._apply_merge_transform(
                [context[f] for f in rule.source_fields],
                rule.parameters
            )
            
        elif rule.transform_type == TransformType.MAP:
            return self._apply_map_transform(value, rule.parameters)
            
        elif rule.transform_type == TransformType.COMPUTE:
            if not context or not all(f in context for f in rule.source_fields):
                raise ValueError("Missing required source fields for compute transform")
            return self._apply_compute_transform(
                {f: context[f] for f in rule.source_fields},
                rule.parameters
            )
            
        elif rule.transform_type == TransformType.CUSTOM:
            if "transform_func" not in rule.parameters:
                raise ValueError("Custom transform requires 'transform_func' parameter")
            return self._apply_custom_transform(value, rule.parameters, context)
            
        raise ValueError(f"Unsupported transform type: {rule.transform_type}")
    
    def _apply_format_transform(
        self,
        value: Any,
        params: Dict[str, Any]
    ) -> Any:
        """Apply format transformation"""
        if not value:
            return value
            
        format_type = params.get("type", "string")
        
        if format_type == "date":
            return self._format_date(
                value,
                params.get("from_format"),
                params.get("to_format", "yyyy-mm-dd")
            )
            
        elif format_type == "number":
            return self._format_number(
                value,
                params.get("decimal_places"),
                params.get("thousands_sep", True)
            )
            
        elif format_type == "string":
            return self._format_string(
                value,
                params.get("case", None),
                params.get("strip", True),
                params.get("max_length", None)
            )
            
        raise ValueError(f"Unsupported format type: {format_type}")
    
    def _apply_split_transform(
        self,
        value: Any,
        params: Dict[str, Any]
    ) -> List[Any]:
        """Split a value into multiple parts"""
        if not value:
            return [None] * len(params.get("target_fields", []))
            
        split_type = params.get("type", "delimiter")
        
        if split_type == "delimiter":
            delimiter = params.get("delimiter", ",")
            parts = str(value).split(delimiter)
            return [p.strip() for p in parts]
            
        elif split_type == "fixed_length":
            lengths = params.get("lengths", [])
            if not lengths:
                raise ValueError("Fixed length split requires 'lengths' parameter")
            value = str(value)
            parts = []
            start = 0
            for length in lengths:
                parts.append(value[start:start + length])
                start += length
            return parts
            
        elif split_type == "regex":
            pattern = params.get("pattern")
            if not pattern:
                raise ValueError("Regex split requires 'pattern' parameter")
            return re.split(pattern, str(value))
            
        raise ValueError(f"Unsupported split type: {split_type}")
    
    def _apply_merge_transform(
        self,
        values: List[Any],
        params: Dict[str, Any]
    ) -> Any:
        """Merge multiple values into one"""
        if not values:
            return None
            
        merge_type = params.get("type", "concat")
        
        if merge_type == "concat":
            delimiter = params.get("delimiter", " ")
            return delimiter.join(str(v) for v in values if v is not None)
            
        elif merge_type == "array":
            return [v for v in values if v is not None]
            
        elif merge_type == "object":
            keys = params.get("keys", [])
            if not keys or len(keys) != len(values):
                raise ValueError("Object merge requires matching keys for values")
            return {k: v for k, v in zip(keys, values) if v is not None}
            
        raise ValueError(f"Unsupported merge type: {merge_type}")
    
    def _apply_map_transform(
        self,
        value: Any,
        params: Dict[str, Any]
    ) -> Any:
        """Map a value to another value"""
        if value is None:
            return params.get("default")
            
        mapping_type = params.get("type", "direct")
        
        if mapping_type == "direct":
            mapping = params.get("mapping", {})
            return mapping.get(str(value), params.get("default"))
            
        elif mapping_type == "boolean":
            return self._map_to_boolean(value)
            
        elif mapping_type == "range":
            ranges = params.get("ranges", [])
            for r in ranges:
                if r["min"] <= float(value) <= r["max"]:
                    return r["value"]
            return params.get("default")
            
        raise ValueError(f"Unsupported mapping type: {mapping_type}")
    
    def _apply_compute_transform(
        self,
        values: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Any:
        """Compute a value from multiple fields"""
        compute_type = params.get("type", "arithmetic")
        
        if compute_type == "arithmetic":
            expression = params.get("expression")
            if not expression:
                raise ValueError("Arithmetic compute requires 'expression' parameter")
            # Safe eval of arithmetic expression
            return eval(
                expression,
                {"__builtins__": {}},
                {k: float(v) if v is not None else 0 for k, v in values.items()}
            )
            
        elif compute_type == "conditional":
            conditions = params.get("conditions", [])
            for condition in conditions:
                if eval(
                    condition["if"],
                    {"__builtins__": {}},
                    values
                ):
                    return condition["then"]
            return params.get("default")
            
        raise ValueError(f"Unsupported compute type: {compute_type}")
    
    def _apply_custom_transform(
        self,
        value: Any,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Apply a custom transformation"""
        transform_func = params["transform_func"]
        if not isinstance(transform_func, str):
            raise ValueError("Custom transform_func must be a string")
            
        # Create a safe environment for eval
        safe_env = {
            "__builtins__": {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "len": len,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "any": any,
                "all": all,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "range": range,
                "abs": abs,
                "pow": pow
            }
        }
        
        # Add context to environment if provided
        if context:
            safe_env.update(context)
        
        # Add the input value
        safe_env["value"] = value
        
        try:
            return eval(transform_func, safe_env)
        except Exception as e:
            raise ValueError(f"Error in custom transform: {str(e)}")
    
    def _format_date(
        self,
        value: str,
        from_format: Optional[str],
        to_format: str
    ) -> str:
        """Format a date string"""
        if not value:
            return value
            
        # Try to detect source format if not specified
        if not from_format:
            for fmt, pattern in self.date_patterns.items():
                if re.match(pattern, value):
                    from_format = fmt
                    break
            if not from_format:
                raise ValueError(f"Could not detect date format for: {value}")
        
        # Parse the date components
        if from_format == "mmddyyyy":
            mm, dd, yyyy = value[:2], value[2:4], value[4:]
        else:
            parts = re.split(r"[-/]", value)
            if len(parts) != 3:
                raise ValueError(f"Invalid date format: {value}")
                
            if from_format.startswith("mm"):
                mm, dd, yyyy = parts
            else:
                yyyy, mm, dd = parts
        
        # Format the output
        if to_format == "yyyy-mm-dd":
            return f"{yyyy}-{mm}-{dd}"
        elif to_format == "mm/dd/yyyy":
            return f"{mm}/{dd}/{yyyy}"
        elif to_format == "mmddyyyy":
            return f"{mm}{dd}{yyyy}"
        
        raise ValueError(f"Unsupported date format: {to_format}")
    
    def _format_number(
        self,
        value: Union[int, float, str],
        decimal_places: Optional[int],
        thousands_sep: bool
    ) -> str:
        """Format a number"""
        if not value:
            return value
            
        try:
            num = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid number: {value}")
            
        if decimal_places is not None:
            num = round(num, decimal_places)
            
        if thousands_sep:
            return "{:,}".format(num)
            
        return str(num)
    
    def _format_string(
        self,
        value: str,
        case: Optional[str],
        strip: bool,
        max_length: Optional[int]
    ) -> str:
        """Format a string"""
        if not value:
            return value
            
        result = str(value)
        
        if strip:
            result = result.strip()
            
        if case == "upper":
            result = result.upper()
        elif case == "lower":
            result = result.lower()
        elif case == "title":
            result = result.title()
            
        if max_length and len(result) > max_length:
            result = result[:max_length]
            
        return result
    
    def _map_to_boolean(self, value: Any) -> bool:
        """Map a value to a boolean"""
        if isinstance(value, bool):
            return value
            
        str_value = str(value).lower().strip()
        
        if str_value in self.bool_mappings[True]:
            return True
        elif str_value in self.bool_mappings[False]:
            return False
            
        raise ValueError(f"Cannot map value to boolean: {value}")
    
    def create_transform_rule(
        self,
        source_value: Any,
        target_schema: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> TransformRule:
        """Create a transform rule based on source value and target schema"""
        source_type = type(source_value).__name__
        target_type = target_schema.get("type", "string")
        
        # Direct copy if types match
        if source_type == target_type:
            return TransformRule(transform_type=TransformType.DIRECT)
        
        # Format transform for type conversions
        if target_type in ["string", "number", "date"]:
            return TransformRule(
                transform_type=TransformType.FORMAT,
                parameters={"type": target_type}
            )
        
        # Map transform for enums
        if "enum" in target_schema:
            return TransformRule(
                transform_type=TransformType.MAP,
                parameters={
                    "type": "direct",
                    "mapping": {str(v): v for v in target_schema["enum"]}
                }
            )
        
        # Boolean conversion
        if target_type == "boolean":
            return TransformRule(
                transform_type=TransformType.MAP,
                parameters={"type": "boolean"}
            )
        
        raise ValueError(
            f"Cannot automatically create transform rule from {source_type} to {target_type}"
        ) 