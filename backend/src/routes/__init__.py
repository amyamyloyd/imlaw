"""Routes package"""

from .pdf_metadata_routes import router as pdf_metadata_routes
from .canonical_field_routes import router as canonical_field_routes
from .field_mapping_routes import router as field_mapping_routes
from .schema_version_routes import router as schema_version_routes
from .form_schema_routes import router as form_schema_routes
from .client_entry_routes import router as client_entry_routes

__all__ = [
    'pdf_metadata_routes',
    'canonical_field_routes',
    'field_mapping_routes',
    'schema_version_routes',
    'form_schema_routes',
    'client_entry_routes'
] 