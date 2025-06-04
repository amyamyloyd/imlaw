from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import sys
from typing import List, Dict, Any
import shutil

# Add the project root to import the FormFieldAnalyzer
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)
from model_analysis.analyze_form_fields import FormFieldAnalyzer

router = APIRouter(prefix="/api/pdf", tags=["PDF Processing"])

@router.post("/upload")
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

@router.post("/save-progress")
async def save_mapping_progress(data: Dict[str, Any]):
    """
    Save field mapping progress to JSON file
    """
    try:
        # Create progress directory if it doesn't exist
        progress_dir = "field_mapping_progress"
        os.makedirs(progress_dir, exist_ok=True)
        
        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mapping_progress_{timestamp}.json"
        filepath = os.path.join(progress_dir, filename)
        
        # Save progress to JSON file
        import json
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return JSONResponse(content={
            "success": True,
            "message": "Progress saved successfully",
            "filepath": filepath
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving progress: {str(e)}")

@router.get("/load-progress/{filename}")
async def load_mapping_progress(filename: str):
    """
    Load previously saved field mapping progress
    """
    try:
        filepath = os.path.join("field_mapping_progress", filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Progress file not found")
        
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return JSONResponse(content={
            "success": True,
            "data": data
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading progress: {str(e)}")

@router.get("/progress-files")
async def list_progress_files():
    """
    List all saved progress files
    """
    try:
        progress_dir = "field_mapping_progress"
        
        if not os.path.exists(progress_dir):
            return JSONResponse(content={
                "success": True,
                "files": []
            })
        
        files = []
        for filename in os.listdir(progress_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(progress_dir, filename)
                stat_info = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "created": stat_info.st_ctime,
                    "size": stat_info.st_size
                })
        
        # Sort by creation time (newest first)
        files.sort(key=lambda x: x['created'], reverse=True)
        
        return JSONResponse(content={
            "success": True,
            "files": files
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing progress files: {str(e)}") 