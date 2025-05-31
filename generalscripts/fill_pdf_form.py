from PyPDFForm import PdfWrapper

# Step 2: Create a PDF wrapper
pdf = PdfWrapper("sample_template.pdf")

# Step 3: Fill the PDF form
filled_pdf = pdf.fill({"field_name": "value", "checkbox_name": True})

# Step 4: Write the filled PDF to an output file
with open("output.pdf", "wb+") as output:
    output.write(filled_pdf.read())

# Optional: Generate coordinate grid for reference
grid_view_pdf = pdf.generate_coordinate_grid(color=(1, 0, 0), margin=100)
with open("output_grid.pdf", "wb+") as output_grid:
    output_grid.write(grid_view_pdf.read())