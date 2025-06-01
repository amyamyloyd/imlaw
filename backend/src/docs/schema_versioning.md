# Schema Versioning System

## Overview
The schema versioning system manages form field schemas across different versions, handling both breaking and non-breaking changes. It supports automatic data migration between versions and maintains a clear migration path for form data.

## Core Components

### VersionedSchemaService
Handles the creation, retrieval, and management of schema versions.

Key features:
- Create new schema versions (draft/released)
- Retrieve specific versions
- Get latest version
- List all versions for a form type

### SchemaMigrationService
Manages the migration of form data between different schema versions.

Key features:
- Create and store migration strategies
- Find migration paths between versions
- Migrate data between versions
- Validate migrations

## Schema Structure
```json
{
  "form_type": "string",
  "version": "major.minor.patch",
  "schema_version": {
    "major": number,
    "minor": number,
    "patch": number,
    "released": datetime
  },
  "fields": [
    {
      "field_id": "string",
      "field_type": "string",
      "field_name": "string",
      "position": {
        "x": number,
        "y": number,
        "width": number,
        "height": number
      },
      "properties": {
        // Field-specific properties
      },
      "flags": {
        "required": boolean
      }
    }
  ],
  "metadata": {
    "draft": boolean,
    "created_by": "string"
  }
}
```

## Version Numbers
- Major (X.0.0): Breaking changes (e.g., field removals, type changes)
- Minor (0.X.0): Non-breaking additions
- Patch (0.0.X): Bug fixes and metadata updates

## Migration Strategy
Migration strategies define how to transform data between versions:
```json
{
  "migration_type": "IN_PLACE | MANUAL",
  "from_version": "string",
  "to_version": "string",
  "field_changes": [
    {
      "field_id": "string",
      "change_type": "added | modified | removed",
      "previous_value": {},
      "new_value": {}
    }
  ]
}
```

## Usage Examples

### Creating a New Schema Version
```python
schema = await schema_service.create_schema(
    form_type="form_type",
    fields=[...],
    draft=True
)
```

### Migrating Data Between Versions
```python
migrated_data = await migration_service.migrate_data(
    form_type="form_type",
    from_version="1.0.0",
    to_version="2.0.0",
    data={...}
)
```

## Testing
Comprehensive tests are available in `scripts/test_schema_versioning.py`, covering:
1. Schema Creation and Versioning
2. Schema Retrieval
3. Migration Path Finding
4. Data Migration
5. Error Handling

## Best Practices
1. Always create schemas in draft mode first
2. Test migrations thoroughly before releasing new versions
3. Use appropriate version numbers based on change type
4. Store migration strategies for all version transitions
5. Validate data before and after migration 