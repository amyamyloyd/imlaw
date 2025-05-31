import PyPDF2
import csv
from PyPDF2.generic import NameObject # For accessing PDF dictionary keys

def extract_label_from_properties(properties_dict):
    """
    Extracts the human-readable label, typically from the /TU (tooltip) key.
    """
    if not isinstance(properties_dict, dict):
        return ""
    
    label = properties_dict.get(NameObject("/TU"))
    if label is None:
        label = properties_dict.get("/TU") # Fallback for plain string key
    
    if isinstance(label, str):
        return label.strip()
    elif label is not None:
        return str(label).strip()
    return ""

# Open the PDF file
pdf_input_path = "i485.pdf" # Or make this a variable you can change
csv_output_path = "i485_field_details.csv"

with open(pdf_input_path, "rb") as pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    fields = reader.get_fields()

# Write field details to a CSV file
with open(csv_output_path, "w", newline='', encoding='utf-8') as csvfile:
    fieldnames = ['PDF Internal ID', 'PDF Field Label (from Tooltip)']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    if fields:
        for pdf_internal_id, field_properties in fields.items():
            pdf_field_label = extract_label_from_properties(field_properties)
            writer.writerow({'PDF Internal ID': pdf_internal_id, 'PDF Field Label (from Tooltip)': pdf_field_label})
    else:
        # If there are no fields, the header will still be written, and the file will be otherwise empty.
        print(f"No fields found in {pdf_input_path}.")

print(f"Field details have been written to {csv_output_path}")