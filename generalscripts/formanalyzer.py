import PyPDF2
import csv

def get_form_fields(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        fields = reader.get_fields()
        return fields

def write_fields_to_csv(fields, csv_path):
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['Field Name', 'Field Properties']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for field_name, field_properties in fields.items():
            writer.writerow({'Field Name': field_name, 'Field Properties': field_properties})

pdf_path = 'i485.pdf'
csv_path = 'formkeys.csv'

fields = get_form_fields(pdf_path)
write_fields_to_csv(fields, csv_path)

print(f"Fields have been written to {csv_path}")