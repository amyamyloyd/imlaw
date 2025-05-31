import os
import json
from copy import deepcopy
from PyPDF2 import PdfReader, PdfWriter

# Load JSON data
with open("i485_filled_output.json", "r") as f:
    data = json.load(f)

# Load original PDF
template_path = "i485.pdf"

for issue_key, fields in data.items():
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    field_map = {item["pdf_internal_id"]: item["value"] for item in fields}

    # Update form fields
    writer.update_page_form_field_values(writer.pages[0], field_map)

    # Save filled form
    output_path = f"{issue_key.lower()}_i485.pdf"
    with open(output_path, "wb") as f_out:
        writer.write(f_out)

    print(f"✅ Saved: {output_path}")

