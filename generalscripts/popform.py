from PyPDFForm import PdfWrapper

# Create a PDF wrapper
pdf = PdfWrapper("sample_template.pdf")

# Fill the PDF form with specified values
filled_pdf = pdf.fill({
    "test_2": "test2 field",
    "test": "testfield",
    "test_3": "test 3 field",
    "check_2": True,
    "check": True,
    "check_3": True
})

# Write the filled PDF to an output file
with open("output2.pdf", "wb+") as output:
    output.write(filled_pdf.read())

print("PDF form has been filled and saved to output2.pdf")