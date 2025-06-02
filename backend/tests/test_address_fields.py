"""Simple test script to verify writing address values to I-485 form."""

import os
from PyPDF2 import PdfReader, PdfWriter

# Test data with address values
field_data = {
    "Pt3Line5_StreetNumberName[0]": "123 Main Street",
    "Pt3Line5_CityOrTown[0]": "Boston", 
    "Pt3Line5_State[0]": "MA",
    "Pt3Line5_ZipCode[0]": "02108"
}

# Get paths
pdf_path = "../../generalscripts/i485.pdf"
output_path = "test_filled.pdf"

# Create PDF reader and writer
reader = PdfReader(pdf_path)
writer = PdfWriter()

# Add all pages from the original PDF
for page in reader.pages:
    writer.add_page(page)

# Write the field values to page 3 (0-based index)
writer.update_page_form_field_values(
    writer.pages[3],  # Page 3 (0-based index)
    field_data
)

# Save the filled PDF
with open(output_path, "wb") as output_file:
    writer.write(output_file)

print(f"\nFilled PDF saved to: {output_path}")

# Verify the fields were written
reader = PdfReader(output_path)
fields = reader.get_fields()

print("\nField values in filled PDF:")
for field_name, value in field_data.items():
    actual_value = fields.get(field_name, {}).get('/V')
    print(f"{field_name}: {actual_value}") 