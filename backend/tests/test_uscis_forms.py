import os
import json
from src.services.pdf_extractor import PDFFormExtractor

def test_uscis_forms():
    """Test PDF extraction with actual USCIS forms"""
    
    # Initialize extractor
    extractor = PDFFormExtractor()
    
    # USCIS forms to test
    forms = [
        "../generalscripts/i485.pdf",
        "../generalscripts/i130.pdf",
        "../generalscripts/i765.pdf",
        "../generalscripts/i693.pdf"
    ]
    
    # Process each form
    for form_path in forms:
        print(f"\nProcessing {os.path.basename(form_path)}:")
        try:
            metadata = extractor.extract_form_metadata(form_path)
            
            print(f"Form type: {metadata['form_type']}")
            print(f"Total fields: {metadata['total_fields']}\n")
            
            # Show sample fields with their labels and tooltips
            print("Sample form fields (showing labels and tooltips):\n")
            
            field_count = 0
            for name, field in metadata['fields'].items():
                # Skip page markers, subforms, and barcodes
                if any(x in name for x in ['#pageSet', '#subform', 'Page', 'BarCode']):
                    continue
                    
                field_count += 1
                if field_count > 5:  # Only show first 5 actual form fields
                    break
                    
                print(f"Field {field_count}:")
                print(f"Internal Name: {field.get('internal_name', 'N/A')}")
                print(f"Type: {field.get('field_type', 'N/A')}")
                print(f"Label: {field.get('label', 'N/A')}")
                print(f"Tooltip: {field.get('tooltip', 'N/A')}")
                print(f"Alternate Name: {field.get('alternate_name', 'N/A')}")
                if field.get('properties'):
                    print("Properties:")
                    for prop, value in field['properties'].items():
                        if value:  # Only show active properties
                            print(f"  - {prop}")
                print()
            
            # Save results for analysis
            output_file = f"test_output_{os.path.splitext(os.path.basename(form_path))[0]}.json"
            with open(output_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"Error processing {form_path}: {str(e)}")
            raise

if __name__ == "__main__":
    test_uscis_forms() 