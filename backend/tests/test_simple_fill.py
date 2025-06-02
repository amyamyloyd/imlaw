"""Simple script to write values directly to I-485 PDF form fields."""

from PyPDF2 import PdfReader, PdfWriter

# The actual field IDs from the I-485 form
test_data = {
    # Basic info fields (we know these work)
    "Pt1Line1a_FamilyName[0]": "GARCIA",
    "Pt1Line1b_GivenName[0]": "MARIA",
    "Pt1Line1c_MiddleName[0]": "ELENA",
    
    # Address fields from Part 3
    "Pt3Line5_StreetNumberName[0]": "123 MAIN STREET",
    "Pt3Line5_CityOrTown[0]": "BOSTON",
    "Pt3Line5_State[0]": "MA",
    "Pt3Line5_ZipCode[0]": "02108",
    
    # Let's try a second address too
    "Pt3Line7_StreetNumberName[0]": "456 OAK AVENUE",
    "Pt3Line7_CityOrTown[0]": "CAMBRIDGE",
    "Pt3Line7_State[0]": "MA",
    "Pt3Line7_ZipCode[0]": "02139"
}

# Read the template PDF
reader = PdfReader("../../generalscripts/i485.pdf")
writer = PdfWriter()

# Add all pages from the original PDF
for page in reader.pages:
    writer.add_page(page)

# Get all form fields
fields = reader.get_fields()

# Write values to fields
for field_name, value in test_data.items():
    if field_name in fields:
        field = fields[field_name]
        field['/V'] = value

# Save the filled PDF
output_path = "simple_test_filled.pdf"
with open(output_path, "wb") as output_file:
    writer.write(output_file)

print(f"\nFilled PDF saved to: {output_path}")

# Verify what was written
reader = PdfReader(output_path)
fields = reader.get_fields()

print("\nField values in filled PDF:")
for field_name, value in test_data.items():
    actual_value = fields.get(field_name, {}).get('/V')
    print(f"{field_name}: Expected={value}, Actual={actual_value}") 