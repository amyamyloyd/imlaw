"""Simple script to write values directly to I-485 PDF form fields using pdfrw."""

from pdfrw import PdfReader, PdfWriter, PdfDict

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
template = PdfReader("../../generalscripts/i485.pdf")

# Fill in the form fields
for page in template.pages:
    if page.Annots:
        for annotation in page.Annots:
            if annotation['/T'] and str(annotation['/T']) in test_data:
                annotation.update(PdfDict(V=test_data[str(annotation['/T'])]))

# Save the filled PDF
output_path = "pdfrw_test_filled.pdf"
PdfWriter().write(output_path, template)

print(f"\nFilled PDF saved to: {output_path}") 