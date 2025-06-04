from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import json
import sys
from typing import List, Dict, Any

# Add the project root to import the FormFieldAnalyzer
sys.path.append(os.path.abspath('.'))
from model_analysis.analyze_form_fields import FormFieldAnalyzer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the analyzer
analyzer = FormFieldAnalyzer()
USCIS_FORMS_DIR = "./uscis_forms"

@app.get("/api/health")
async def health():
    return {"status": "healthy", "message": "Backend is running!"}

@app.get("/api/forms/available")
async def get_available_forms():
    """Get list of available PDF forms"""
    try:
        forms = []
        for filename in os.listdir(USCIS_FORMS_DIR):
            if filename.endswith('.pdf'):
                form_id = filename.replace('.pdf', '')
                filled_file = os.path.join(USCIS_FORMS_DIR, f"filled_{form_id}.json")
                forms.append({
                    "id": form_id,
                    "name": filename,
                    "display_name": form_id.upper().replace('I', 'I-'),
                    "has_saved_data": os.path.exists(filled_file)
                })
        return {"forms": forms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forms/{form_id}/analyze")
async def analyze_form(form_id: str):
    """Analyze a specific form and return fields with any saved data"""
    try:
        form_path = os.path.join(USCIS_FORMS_DIR, f"{form_id}.pdf")
        if not os.path.exists(form_path):
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Extract fields using existing analyzer
        form_fields = analyzer.analyze_form(form_path, f"{form_id}.pdf")
        
        # Convert to list format
        fields = []
        for field_name, field_data in form_fields.items():
            fields.append({
                "field_name": field_name,
                "form_id": form_id,
                "tooltip": field_data.get("tooltip", ""),
                "type": field_data.get("type", ""),
                "page": field_data.get("page", 0),
                "persona": field_data.get("persona"),
                "domain": field_data.get("domain"),
                "screen_label": field_data.get("screen_label"),
                "value_info": field_data.get("value_info"),
                # Add mapping fields
                "mapped_collection_field": None,
                "is_new_collection_field": False
            })
        
        # Load saved data if it exists
        filled_file = os.path.join(USCIS_FORMS_DIR, f"filled_{form_id}.json")
        if os.path.exists(filled_file):
            with open(filled_file, 'r') as f:
                saved_data = json.load(f)
                saved_fields = {field["field_name"]: field for field in saved_data.get("fields", [])}
                
                # Merge saved data with extracted fields
                for field in fields:
                    if field["field_name"] in saved_fields:
                        saved_field = saved_fields[field["field_name"]]
                        field["persona"] = saved_field.get("persona", field["persona"])
                        field["domain"] = saved_field.get("domain", field["domain"])
                        field["mapped_collection_field"] = saved_field.get("mapped_collection_field")
                        field["is_new_collection_field"] = saved_field.get("is_new_collection_field", False)
        
        return {
            "success": True,
            "form_id": form_id,
            "field_count": len(fields),
            "fields": fields
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forms/{form_id}/save-field")
async def save_field_mapping(form_id: str, field_data: Dict[str, Any]):
    """Save individual field mapping data"""
    try:
        filled_file = os.path.join(USCIS_FORMS_DIR, f"filled_{form_id}.json")
        
        # Load existing data or create new
        if os.path.exists(filled_file):
            with open(filled_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"form_id": form_id, "fields": []}
        
        # Update or add field
        field_name = field_data["field_name"]
        existing_field = None
        for i, field in enumerate(data["fields"]):
            if field["field_name"] == field_name:
                existing_field = i
                break
        
        if existing_field is not None:
            data["fields"][existing_field] = field_data
        else:
            data["fields"].append(field_data)
        
        # Save back to file
        with open(filled_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {"success": True, "message": "Field saved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collection-fields")
async def get_collection_fields():
    """Get available collection fields for mapping"""
    # For now, return some common collection fields
    # In the future, this could be dynamic based on existing mappings
    return {
        "fields": [
            "applicant_first_name",
            "applicant_last_name", 
            "applicant_date_of_birth",
            "applicant_address_street",
            "applicant_address_city",
            "applicant_address_state",
            "applicant_address_zip",
            "applicant_phone",
            "applicant_email",
            "beneficiary_first_name",
            "beneficiary_last_name",
            "beneficiary_date_of_birth",
            "spouse_first_name",
            "spouse_last_name",
            "employer_name",
            "employer_address"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000) 