"""Schema migration service"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, UTC
from enum import Enum
from pydantic import BaseModel
from bson import ObjectId

from src.db.database import Database
from src.models.versioned_form_schema import VersionedFormSchema, SchemaVersion, FieldChange
from src.services.versioned_schema_service import VersionedSchemaService
from src.models.form_schema import FormSchema, FormFieldDefinition
from src.models.versioned_form_schema import VersionDiff, ChangeType

class MigrationType(str, Enum):
    """Types of schema migrations"""
    IN_PLACE = "in-place"  # Immediate update of all documents
    LAZY = "lazy"          # Update documents when accessed
    MANUAL = "manual"      # Requires manual intervention

class MigrationStrategy(BaseModel):
    """Strategy for migrating form data between schema versions"""
    field_mappings: Dict[str, str]  # old_field_id -> new_field_id
    value_transformations: Dict[str, Dict[str, Any]]  # field_id -> transformation rules
    validation_updates: Dict[str, Dict[str, Any]]  # field_id -> new validation rules

class SchemaMigrationService:
    """Service for migrating form data between schema versions"""
    
    def __init__(self, db=None):
        self.db = db
        self.migration_strategies: Dict[str, Dict[str, MigrationStrategy]] = {}  # form_type -> {version_pair -> strategy}
        if db:
            self.migrations_collection = self.db.get_collection("schema_migrations")
            self._ensure_indexes()
        
    def _ensure_indexes(self):
        """Ensure required indexes exist in the database"""
        if self.db:
            self.migrations_collection.create_index([
                ("form_type", 1),
                ("from_version", 1),
                ("to_version", 1)
            ], unique=True)
        
    async def create_migration_strategy(
        self,
        form_type: str,
        from_version: str,
        to_version: str,
        field_changes: List[FieldChange],
        breaking_changes: bool = False
    ) -> MigrationStrategy:
        """Create a migration strategy based on field changes"""
        strategy = MigrationStrategy(
            migration_type=MigrationType.MANUAL if breaking_changes else MigrationType.IN_PLACE,
            from_version=from_version,
            to_version=to_version
        )
        
        # Analyze field changes to determine mappings and transformations
        for change in field_changes:
            if change.change_type == "modified":
                # Field was modified - may need transformation
                old_field = change.previous_value
                new_field = change.new_value
                
                # Check if field type changed
                if old_field["field_type"] != new_field["field_type"]:
                    strategy.transformations[change.field_id] = {
                        "from_type": old_field["field_type"],
                        "to_type": new_field["field_type"],
                        "conversion_required": True
                    }
                
                # Check if validation rules changed
                if old_field.get("properties", {}) != new_field.get("properties", {}):
                    strategy.validation_rules[change.field_id] = new_field.get("properties", {})
                    
            elif change.change_type == "removed":
                # Field was removed - mark for deletion
                strategy.field_mappings[change.field_id] = None
                
            elif change.change_type == "added":
                # New field - check properties for default value and required flag
                field_props = change.new_value.get("properties", {})
                if "default" in field_props:
                    strategy.transformations[change.field_id] = {
                        "default_value": field_props["default"]
                    }
                elif field_props.get("required", False):
                    strategy.transformations[change.field_id] = {
                        "required": True
                    }
                
                # Add validation rules if any
                if field_props:
                    strategy.validation_rules[change.field_id] = field_props
        
        return strategy
    
    async def store_migration_strategy(
        self,
        form_type: str,
        strategy: MigrationStrategy
    ) -> str:
        """Store a migration strategy in the database"""
        document = {
            "form_type": form_type,
            "from_version": strategy.from_version,
            "to_version": strategy.to_version,
            "migration_type": strategy.migration_type,
            "field_mappings": strategy.field_mappings,
            "transformations": strategy.transformations,
            "validation_rules": strategy.validation_rules,
            "created_at": datetime.utcnow()
        }
        
        result = await self.migrations_collection.insert_one(document)
        return str(result.inserted_id)
    
    async def get_migration_path(
        self,
        form_type: str,
        from_version: str,
        to_version: str
    ) -> List[MigrationStrategy]:
        """Find a path of migrations between two versions"""
        if from_version == to_version:
            return []
            
        # Get all migrations for this form type
        cursor = self.migrations_collection.find({
            "form_type": form_type
        })
        migrations = await cursor.to_list(length=None)
        
        # Build a graph of version transitions
        graph = {}
        for migration in migrations:
            if migration["from_version"] not in graph:
                graph[migration["from_version"]] = {}
            graph[migration["from_version"]][migration["to_version"]] = MigrationStrategy(
                migration_type=migration["migration_type"],
                from_version=migration["from_version"],
                to_version=migration["to_version"],
                field_mappings=migration["field_mappings"],
                transformations=migration["transformations"],
                validation_rules=migration["validation_rules"]
            )
        
        # Use BFS to find shortest path
        queue = [(from_version, [])]
        visited = {from_version}
        
        while queue:
            current_version, path = queue.pop(0)
            
            if current_version == to_version:
                return path
                
            if current_version in graph:
                for next_version, strategy in graph[current_version].items():
                    if next_version not in visited:
                        visited.add(next_version)
                        queue.append((next_version, path + [strategy]))
        
        return []  # No path found
    
    async def validate_migration(
        self,
        form_type: str,
        from_version: str,
        to_version: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate if data can be migrated between versions"""
        path = await self.get_migration_path(form_type, from_version, to_version)
        if not path:
            return False, ["No migration path found"]
            
        errors = []
        current_data = data.copy()
        
        # Apply each migration in the path
        for strategy in path:
            # Check field mappings
            for old_field, new_field in strategy.field_mappings.items():
                if new_field is None and old_field in current_data:
                    del current_data[old_field]
                elif new_field and old_field in current_data:
                    current_data[new_field] = current_data.pop(old_field)
            
            # Check required fields and defaults
            for field_id, rules in strategy.transformations.items():
                if field_id not in current_data:
                    if rules.get("required", False) and "default_value" not in rules:
                        errors.append(f"Required field {field_id} missing with no default")
                elif rules.get("conversion_required"):
                    try:
                        _ = self._convert_field_value(
                            current_data[field_id],
                            rules["from_type"],
                            rules["to_type"]
                        )
                    except ValueError:
                        errors.append(f"Field {field_id} requires type conversion")
            
            # Check validation rules after potential conversions and cleaning
            for field_id, rules in strategy.validation_rules.items():
                # First check if the field is required and missing
                if rules.get("required", False):
                    has_default = (field_id in strategy.transformations and 
                                 "default_value" in strategy.transformations[field_id])
                    if field_id not in current_data and not has_default:
                        errors.append(f"Required field {field_id} missing with no default")
                        continue
                
                if field_id in current_data:
                    value = current_data[field_id]
                    
                    # If there's a type conversion, validate against the new type
                    if field_id in strategy.transformations and strategy.transformations[field_id].get("conversion_required"):
                        try:
                            value = self._convert_field_value(
                                value,
                                strategy.transformations[field_id]["from_type"],
                                strategy.transformations[field_id]["to_type"]
                            )
                        except ValueError:
                            continue  # Skip validation if conversion would fail
                    
                    # Clean the value first (e.g., truncate if too long)
                    try:
                        value = self._validate_and_clean_value(value, rules)
                    except ValueError as e:
                        errors.append(str(e))
                        continue
                    
                    # Now validate the cleaned value
                    if isinstance(value, str):
                        if "minLength" in rules and len(value) < rules["minLength"]:
                            errors.append(f"Field {field_id} below minimum length")
                        if "pattern" in rules:
                            import re
                            if not re.match(rules["pattern"], value):
                                errors.append(f"Field {field_id} does not match required pattern")
                    elif isinstance(value, (int, float)):
                        if "minimum" in rules and value < rules["minimum"]:
                            errors.append(f"Field {field_id} below minimum value")
                        if "maximum" in rules and value > rules["maximum"]:
                            errors.append(f"Field {field_id} exceeds maximum value")
        
        return len(errors) == 0, errors
    
    async def migrate_data(
        self,
        form_type: str,
        from_version: str,
        to_version: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Migrate data from one schema version to another"""
        # First validate the migration
        is_valid, errors = await self.validate_migration(form_type, from_version, to_version, data)
        if not is_valid:
            raise ValueError(f"Migration validation failed: {', '.join(errors)}")
            
        path = await self.get_migration_path(form_type, from_version, to_version)
        if not path:
            raise ValueError("No migration path found")
            
        current_data = data.copy()
        
        # Apply each migration in the path
        for strategy in path:
            # Apply field mappings
            for old_field, new_field in strategy.field_mappings.items():
                if new_field is None and old_field in current_data:
                    del current_data[old_field]
                elif new_field and old_field in current_data:
                    current_data[new_field] = current_data.pop(old_field)
            
            # Apply transformations
            for field_id, rules in strategy.transformations.items():
                # Handle field additions and defaults
                if field_id not in current_data:
                    if "default_value" in rules:
                        current_data[field_id] = rules["default_value"]
                    elif rules.get("properties", {}).get("default"):
                        current_data[field_id] = rules["properties"]["default"]
                    elif rules.get("required", False):
                        raise ValueError(f"Required field {field_id} missing with no default")
                
                # Handle type conversions
                if rules.get("conversion_required") and field_id in current_data:
                    current_data[field_id] = self._convert_field_value(
                        current_data[field_id],
                        rules["from_type"],
                        rules["to_type"]
                    )
            
            # Apply validation rules and clean data
            for field_id, rules in strategy.validation_rules.items():
                if field_id in current_data:
                    current_data[field_id] = self._validate_and_clean_value(
                        current_data[field_id],
                        rules
                    )
                elif rules.get("required", False) and field_id not in strategy.transformations:
                    raise ValueError(f"Required field {field_id} missing with no default")
        
        return current_data
    
    def _convert_field_value(self, value: Any, from_type: str, to_type: str) -> Any:
        """Convert a value from one type to another"""
        if from_type == to_type:
            return value
            
        if to_type == "number":
            try:
                if isinstance(value, str) and value.strip().isdigit():
                    return int(value)
                elif isinstance(value, str) and "." in value:
                    return float(value)
                elif isinstance(value, (int, float)):
                    return value
                else:
                    raise ValueError(f"Cannot convert '{value}' to number")
            except ValueError:
                raise ValueError(f"Invalid number format: {value}")
                
        elif to_type == "string":
            return str(value)
            
        elif to_type == "boolean":
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                value = value.lower()
                if value in ("true", "1", "yes"):
                    return True
                elif value in ("false", "0", "no"):
                    return False
            elif isinstance(value, (int, float)):
                return bool(value)
            raise ValueError(f"Cannot convert '{value}' to boolean")
            
        elif to_type == "array":
            if isinstance(value, (list, tuple)):
                return list(value)
            elif isinstance(value, str):
                return [item.strip() for item in value.split(",")]
            raise ValueError(f"Cannot convert '{value}' to array")
            
        elif to_type == "object":
            if isinstance(value, dict):
                return value
            raise ValueError(f"Cannot convert '{value}' to object")
            
        raise ValueError(f"Unsupported type conversion: {from_type} -> {to_type}")
    
    def _validate_and_clean_value(self, value: Any, rules: Dict[str, Any]) -> Any:
        """Clean and validate a field value according to rules"""
        if value is None:
            if rules.get("required", False):
                raise ValueError("Required field cannot be None")
            return value
            
        # Handle string fields
        if isinstance(value, str):
            # Truncate if too long
            if "maxLength" in rules and len(value) > rules["maxLength"]:
                value = value[:rules["maxLength"]]
            return value
            
        # Handle numeric fields
        if isinstance(value, (int, float)):
            if "minimum" in rules:
                value = max(value, rules["minimum"])
            if "maximum" in rules:
                value = min(value, rules["maximum"])
            return value
            
        return value 

    def register_migration_strategy(self, form_type: str, from_version: str, to_version: str, strategy: MigrationStrategy) -> None:
        """Register a migration strategy for a specific form type and version pair"""
        if form_type not in self.migration_strategies:
            self.migration_strategies[form_type] = {}
        
        version_pair = f"{from_version}->{to_version}"
        self.migration_strategies[form_type][version_pair] = strategy
        
        if self.db:
            # Store in database
            self.migrations_collection.update_one(
                {
                    "form_type": form_type,
                    "from_version": from_version,
                    "to_version": to_version
                },
                {
                    "$set": {
                        "strategy": strategy.model_dump(),
                        "updated_at": datetime.now(UTC)
                    }
                },
                upsert=True
            )
    
    def get_migration_strategy(self, form_type: str, from_version: str, to_version: str) -> Optional[MigrationStrategy]:
        """Get the migration strategy for a specific form type and version pair"""
        # First try in-memory cache
        if form_type in self.migration_strategies:
            version_pair = f"{from_version}->{to_version}"
            if version_pair in self.migration_strategies[form_type]:
                return self.migration_strategies[form_type][version_pair]
        
        # If not found and we have a db connection, try database
        if self.db:
            strategy_doc = self.migrations_collection.find_one({
                "form_type": form_type,
                "from_version": from_version,
                "to_version": to_version
            })
            
            if strategy_doc:
                strategy = MigrationStrategy(**strategy_doc["strategy"])
                # Cache in memory
                if form_type not in self.migration_strategies:
                    self.migration_strategies[form_type] = {}
                version_pair = f"{from_version}->{to_version}"
                self.migration_strategies[form_type][version_pair] = strategy
                return strategy
        
        return None
    
    def migrate_form_data(self, form_type: str, from_version: str, to_version: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate form data from one schema version to another"""
        strategy = self.get_migration_strategy(form_type, from_version, to_version)
        if not strategy:
            # If no explicit strategy is found, try to generate one from version diff
            strategy = self._generate_migration_strategy(form_type, from_version, to_version)
        
        if not strategy:
            raise ValueError(f"No migration strategy found for {form_type} from version {from_version} to {to_version}")
        
        migrated_data = {}
        
        # Apply field mappings
        for old_field_id, new_field_id in strategy.field_mappings.items():
            if old_field_id in form_data:
                migrated_data[new_field_id] = form_data[old_field_id]
        
        # Apply value transformations
        for field_id, transformations in strategy.value_transformations.items():
            if field_id in migrated_data:
                value = migrated_data[field_id]
                for transform_type, transform_rule in transformations.items():
                    if transform_type == "format":
                        value = self._apply_format_transformation(value, transform_rule)
                    elif transform_type == "validation":
                        value = self._apply_validation_transformation(value, transform_rule)
                migrated_data[field_id] = value
        
        # Apply validation updates
        for field_id, validation_rules in strategy.validation_updates.items():
            if field_id in migrated_data:
                value = migrated_data[field_id]
                migrated_data[field_id] = self._apply_validation_transformation(value, validation_rules)
        
        return migrated_data
    
    def _generate_migration_strategy(self, form_type: str, from_version: str, to_version: str) -> Optional[MigrationStrategy]:
        """Generate a migration strategy from version diff"""
        # This would be implemented to analyze the version diff and generate a strategy
        # For now, return None to indicate no automatic strategy available
        return None
    
    def _apply_format_transformation(self, value: Any, transform_rule: Dict[str, Any]) -> Any:
        """Apply format transformation to a field value"""
        if transform_rule.get("type") == "date":
            # Example: Convert date format
            old_format = transform_rule.get("from_format", "%Y-%m-%d")
            new_format = transform_rule.get("to_format", "%d/%m/%Y")
            if isinstance(value, str):
                try:
                    date_obj = datetime.strptime(value, old_format)
                    return date_obj.strftime(new_format)
                except ValueError:
                    return value
        return value
    
    def _apply_validation_transformation(self, value: Any, transform_rule: Dict[str, Any]) -> Any:
        """Apply validation transformation to a field value"""
        if transform_rule.get("type") == "length":
            # Example: Truncate value to max length
            max_length = transform_rule.get("max_length")
            if isinstance(value, str) and max_length and len(value) > max_length:
                return value[:max_length]
        return value 