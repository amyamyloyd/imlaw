from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
import sys
import shutil
from typing import Dict, Any
import json
from datetime import datetime

# Add the parent directory to import the FormFieldAnalyzer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model_analysis.analyze_form_fields import FormFieldAnalyzer

app = FastAPI(title="PDF Field Mapper API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/pdf/upload")
async def upload_and_extract_fields(file: UploadFile = File(...)):
    """
    Upload a PDF and extract all form fields with metadata using FormFieldAnalyzer
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create temporary file to save uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        try:
            # Save uploaded file to temporary location
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
            
            # Initialize the FormFieldAnalyzer
            analyzer = FormFieldAnalyzer()
            
            # Extract fields using existing analyzer
            form_fields = analyzer.analyze_form(temp_file_path, file.filename)
            
            # Convert to the format expected by frontend
            field_list = []
            for field_name, field_data in form_fields.items():
                field_list.append({
                    "name": field_data["name"],
                    "type": field_data["type"],
                    "tooltip": field_data.get("tooltip", ""),
                    "page": field_data.get("page", 0),
                    "persona": field_data.get("persona"),
                    "domain": field_data.get("domain"), 
                    "screen_label": field_data.get("screen_label"),
                    "value_info": field_data.get("value_info"),
                    "hierarchy": field_data.get("hierarchy", {})
                })
            
            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "field_count": len(field_list),
                "fields": field_list
            })
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

@app.post("/api/pdf/save-progress")
async def save_mapping_progress(data: Dict[str, Any]):
    """
    Save field mapping progress to JSON file
    """
    try:
        # Create progress directory if it doesn't exist
        progress_dir = "field_mapping_progress"
        os.makedirs(progress_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mapping_progress_{timestamp}.json"
        filepath = os.path.join(progress_dir, filename)
        
        # Save progress to JSON file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return JSONResponse(content={
            "success": True,
            "message": "Progress saved successfully",
            "filepath": filepath
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving progress: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 