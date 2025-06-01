from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from config.database import Database
from routes.pdf_metadata_routes import router as pdf_metadata_router

app = FastAPI(
    title="ImLaw API",
    description="API for immigration law document management system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database connection
@app.on_event("startup")
async def startup_event():
    Database.initialize()

# Include routers
app.include_router(pdf_metadata_router)

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