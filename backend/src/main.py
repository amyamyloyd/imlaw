"""Main application module"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from routes import (
    schema_version_routes,
    pdf_metadata_routes,
    canonical_field_routes,
    field_mapping_routes,
    form_schema_routes,
    client_entry_routes,
    document_management_routes,
    pdf_field_routes
)
from db.indexes import create_indexes

# Initialize test environment if running tests
if "PYTEST_CURRENT_TEST" in os.environ:
    from config.test_config import get_test_db
    os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/imlaw_test'
    os.environ['MONGODB_DB_NAME'] = 'imlaw_test'
    os.environ['JWT_SECRET'] = 'test-secret-key'
    os.environ['JWT_ALGORITHM'] = 'HS256'
    os.environ['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'] = '30'

# Create FastAPI application with enhanced documentation
app = FastAPI(
    title="ImLaw API",
    description="""
    ImLaw Backend API for managing immigration law document processing.
    
    Key features:
    * Document Management - Upload, track, and manage client documents
    * Form Schemas - Define and version form structures
    * PDF Processing - Extract and validate form data
    * Client Data - Manage client profiles and form submissions
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "ImLaw Support",
        "email": "support@imlaw.com"
    },
    license_info={
        "name": "Proprietary",
        "identifier": "ImLaw-1.0"
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(schema_version_routes.router)
app.include_router(pdf_metadata_routes.router)
app.include_router(canonical_field_routes.router)
app.include_router(field_mapping_routes.router)
app.include_router(form_schema_routes.router)
app.include_router(client_entry_routes.router)
app.include_router(document_management_routes.router)
app.include_router(pdf_field_routes.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database indexes and connections on startup."""
    await create_indexes()

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 