from typing import Dict, Any
from datetime import datetime

class CanonicalFieldCollection:
    """MongoDB collection configuration for canonical fields"""
    name = "canonical_fields"
    
    # Collection indexes
    indexes = [
        {
            "keys": [("field_name", 1)],
            "unique": True,
            "name": "unique_field_name"
        },
        {
            "keys": [("category", 1)],
            "name": "category_lookup"
        },
        {
            "keys": [("group_name", 1)],
            "name": "group_lookup"
        },
        {
            "keys": [
                ("form_mappings.form_type", 1),
                ("form_mappings.form_version", 1)
            ],
            "name": "form_mappings"
        },
        {
            "keys": [("aliases", 1)],
            "name": "aliases_lookup"
        },
        {
            "keys": [("parent_field", 1)],
            "name": "parent_lookup"
        },
        {
            "keys": [("created_at", -1)],
            "name": "creation_date"
        }
    ]
    
    # MongoDB schema validation
    validation = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "field_name",
                "display_name",
                "data_type",
                "created_at",
                "updated_at"
            ],
            "properties": {
                "field_name": {
                    "bsonType": "string",
                    "pattern": "^[a-z][a-z0-9_]*$",
                    "description": "Must be lowercase alphanumeric with underscores, starting with a letter"
                },
                "display_name": {
                    "bsonType": "string",
                    "minLength": 1,
                    "description": "Human-readable field name"
                },
                "description": {
                    "bsonType": ["string", "null"],
                    "description": "Optional field description"
                },
                "data_type": {
                    "enum": ["string", "number", "date", "boolean", "array", "object"],
                    "description": "Field data type"
                },
                "validation_rules": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["rule_type", "parameters"],
                        "properties": {
                            "rule_type": {
                                "bsonType": "string"
                            },
                            "parameters": {
                                "bsonType": "object"
                            },
                            "error_message": {
                                "bsonType": ["string", "null"]
                            }
                        }
                    }
                },
                "form_mappings": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": [
                            "form_type",
                            "form_version",
                            "field_id",
                            "mapping_type",
                            "created_at",
                            "updated_at"
                        ],
                        "properties": {
                            "form_type": {
                                "bsonType": "string",
                                "pattern": "^[A-Z][A-Z0-9-]*$"
                            },
                            "form_version": {
                                "bsonType": "string",
                                "minLength": 1
                            },
                            "field_id": {
                                "bsonType": "string",
                                "minLength": 1
                            },
                            "mapping_type": {
                                "enum": ["direct", "transform", "composite"]
                            },
                            "transform_logic": {
                                "bsonType": ["string", "null"]
                            },
                            "notes": {
                                "bsonType": ["string", "null"]
                            },
                            "created_at": {
                                "bsonType": "date"
                            },
                            "updated_at": {
                                "bsonType": "date"
                            }
                        }
                    }
                },
                "category": {
                    "bsonType": ["string", "null"],
                    "description": "Optional field category"
                },
                "required": {
                    "bsonType": "bool",
                    "description": "Whether the field is typically required"
                },
                "parent_field": {
                    "bsonType": ["string", "null"],
                    "description": "Optional parent field name"
                },
                "group_name": {
                    "bsonType": ["string", "null"],
                    "description": "Optional logical group name"
                },
                "dependencies": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "string"
                    },
                    "description": "List of field dependencies"
                },
                "created_at": {
                    "bsonType": "date",
                    "description": "Creation timestamp"
                },
                "updated_at": {
                    "bsonType": "date",
                    "description": "Last update timestamp"
                },
                "aliases": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "string"
                    },
                    "description": "Alternative field names"
                },
                "source_priority": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "string"
                    },
                    "description": "Preferred data sources in priority order"
                },
                "validation_history": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["timestamp", "changed_by"],
                        "properties": {
                            "timestamp": {
                                "bsonType": "date"
                            },
                            "changed_by": {
                                "bsonType": "string"
                            },
                            "previous_rules": {
                                "bsonType": "array"
                            },
                            "new_rules": {
                                "bsonType": "array"
                            },
                            "reason": {
                                "bsonType": ["string", "null"]
                            }
                        }
                    }
                },
                "usage_stats": {
                    "bsonType": "object",
                    "required": ["total_uses", "error_count"],
                    "properties": {
                        "total_uses": {
                            "bsonType": "int",
                            "minimum": 0
                        },
                        "last_used": {
                            "bsonType": ["date", "null"]
                        },
                        "form_usage": {
                            "bsonType": "object",
                            "patternProperties": {
                                "^.*$": {
                                    "bsonType": "int",
                                    "minimum": 0
                                }
                            }
                        },
                        "error_count": {
                            "bsonType": "int",
                            "minimum": 0
                        }
                    }
                },
                "metadata": {
                    "bsonType": "object",
                    "description": "Additional metadata"
                }
            }
        }
    } 