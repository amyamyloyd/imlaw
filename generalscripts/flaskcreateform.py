from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
import fitz  # PyMuPDF

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client['myspdb']
i90samples = db['i90samples']

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    form_data = {
        "P1_Line3a_FamilyName": request.form['P1_Line3a_FamilyName'],
        "P1_Line3b_GivenName": request.form['P1_Line3b_GivenName'],
        "P1_Line3c_MiddleName": request.form['P1_Line3c_MiddleName'],
        "P1_Line6a_InCareOfName": request.form['P1_Line6a_InCareOfName'],
        "P1_Line6b_StreetNumberName": request.form['P1_Line6b_StreetNumberName'],
        "P1_Line6c_AptSteFlrNumber": request.form['P1_Line6c_AptSteFlrNumber'],
        "P1_Line6d_CityOrTown": request.form['P1_Line6d_CityOrTown'],
        "P1_Line6e_State": request.form['P1_Line6e_State'],
        "P1_Line6f_ZipCode": request.form['P1_Line6f_ZipCode'],
        "P1_Line6g_Province": request.form['P1_Line6g_Province'],
        "P1_Line6i_Country": request.form['P1_Line6i_Country'],
        "P1_Line5a_FamilyName": request.form['P1_Line5a_FamilyName'],
        "P1_Line5b_GivenName": request.form['P1_Line5b_GivenName'],
        "P1_Line5c_MiddleName": request.form['P1_Line5c_MiddleName']
    }

    # Insert form data into MongoDB
    i90samples.insert_one(form_data)

    # Populate and save the Adobe PDF form
    input_pdf_path = 'Form i90.pdf'
    output_pdf_path = f"{form_data['P1_Line3b_GivenName']}_i90.pdf"
    try:
        data = form_data
        doc = fitz.open(input_pdf_path)
        page = doc.load_page(0)
        
        # Debug: Print all field names and values in the form
        for field in page.widgets():
            print(f"Field name: {field.field_name}, Current value: {field.field_value}")
        
        for field in page.widgets():
            field_name = field.field_name
            if field_name in data:
                print(f"Updating field {field_name} to {data[field_name]}")  # Debug: Print which fields are being updated
                field.field_value = data[field_name]
                field.update()
                
        doc.save(output_pdf_path)
        doc.close()
        print(f"PDF successfully written to {output_pdf_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)