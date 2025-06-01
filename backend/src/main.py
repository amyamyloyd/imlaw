from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import (
    pdf_metadata_routes,
    canonical_field_routes,
    field_mapping_routes,
    form_schema_routes,
    client_entry_routes
)
from .db.indexes import create_indexes

app = FastAPI(
    title="Immigration Forms API",
    description="API for managing immigration form schemas and field mappings",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(pdf_metadata_routes.router)
app.include_router(canonical_field_routes.router)
app.include_router(field_mapping_routes.router)
app.include_router(form_schema_routes.router)
app.include_router(client_entry_routes.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database indexes and validation rules"""
    await create_indexes()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "imlaw-api"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 