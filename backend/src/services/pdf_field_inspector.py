from PyPDF2 import PdfReader
import os
import json

def inspect_pdf_fields(pdf_path: str):
    """Print all form field names from a PDF"""
    try:
        reader = PdfReader(pdf_path)
        
        print(f"\nInspecting PDF fields in: {pdf_path}")
        print("=" * 50)
        
        if '/AcroForm' not in reader.trailer['/Root']:
            print("This PDF does not contain any form fields!")
            return
            
        fields = reader.get_form_text_fields()
        print(f"\nFound {len(fields)} form fields:")
        print("-" * 30)
        
        # Print fields in a formatted way
        for field_name in sorted(fields.keys()):
            print(f"Field: {field_name}")
            print(f"Current Value: {fields[field_name]}")
            print("-" * 30)
            
        # Save fields to JSON for reference
        output_json = pdf_path.replace('.pdf', '_fields.json')
        with open(output_json, 'w') as f:
            json.dump(fields, f, indent=2)
        print(f"\nSaved field names to: {output_json}")
        
    except Exception as e:
        print(f"Error inspecting PDF: {str(e)}")

if __name__ == "__main__":
    # Get the path to our test PDF
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "tests", "data", "pdfs", "i485.pdf")
    inspect_pdf_fields(pdf_path) 