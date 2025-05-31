from pymongo import MongoClient, errors

# Connection URI
uri = "mongodb://localhost:27017/"

# Connect to MongoDB
try:
    client = MongoClient(uri)
    db = client['myspdb']
    print("Connected to MongoDB successfully")
except errors.ConnectionError as e:
    print(f"Error connecting to MongoDB: {e}")

# Create collections and insert sample documents
try:
    # Applicants Collection
    applicants = db['applicants']
    applicants.insert_one({
        "applicant_id": "applicant_1",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "ssn": "123-45-6789",
        "email": "john.doe@example.com",
        "phone_number": "555-1234"
    })
    
    # Addresses Collection
    addresses = db['addresses']
    addresses.insert_one({
        "address_id": "address_1",
        "applicant_id": "applicant_1",
        "type": "primary_residence",
        "address_line1": "123 Main St",
        "address_line2": "Apt 4B",
        "city": "Somewhere",
        "state": "CA",
        "zip_code": "12345",
        "country": "USA",
        "start_date": "2000-01-01",
        "end_date": "2010-01-01"
    })
    
    # Family Members Collection
    family_members = db['family_members']
    family_members.insert_one({
        "family_member_id": "family_member_1",
        "applicant_id": "applicant_1",
        "relationship": "spouse",
        "role": "beneficiary",
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1982-02-02",
        "ssn": "987-65-4321",
        "email": "jane.doe@example.com",
        "phone_number": "555-6789"
    })
    
    # Employment History Collection
    employment_history = db['employment_history']
    employment_history.insert_one({
        "employment_id": "employment_1",
        "applicant_id": "applicant_1",
        "employer_name": "Company Inc.",
        "position": "Software Engineer",
        "address": {
            "address_line1": "456 Corporate Dr",
            "city": "Techville",
            "state": "TX",
            "zip_code": "67890",
            "country": "USA"
        },
        "start_date": "2010-02-01",
        "end_date": "2020-02-01"
    })
    
    # Academic History Collection
    academic_history = db['academic_history']
    academic_history.insert_one({
        "academic_id": "academic_1",
        "applicant_id": "applicant_1",
        "institution_name": "University of Example",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        "start_date": "1998-09-01",
        "end_date": "2002-05-01",
        "gpa": "3.8"
    })
    
    # Medical Conditions Collection
    medical_conditions = db['medical_conditions']
    medical_conditions.insert_one({
        "medical_id": "medical_1",
        "applicant_id": "applicant_1",
        "condition_name": "Diabetes",
        "diagnosis_date": "2005-03-01",
        "treatment_description": "Insulin therapy",
        "physician_name": "Dr. Smith",
        "physician_contact": "555-5678"
    })
    
    # Criminal History Collection
    criminal_history = db['criminal_history']
    criminal_history.insert_one({
        "criminal_id": "criminal_1",
        "applicant_id": "applicant_1",
        "offense": "Theft",
        "conviction_date": "2008-06-01",
        "sentence": "1 year probation",
        "court_name": "Example County Court",
        "court_address": {
            "address_line1": "789 Court St",
            "city": "Lawtown",
            "state": "TX",
            "zip_code": "78901",
            "country": "USA"
        }
    })
    
    # Exceptional Skills Collection
    exceptional_skills = db['exceptional_skills']
    exceptional_skills.insert_one({
        "skill_id": "skill_1",
        "applicant_id": "applicant_1",
        "skill_name": "Piano Virtuoso",
        "description": "Award-winning pianist with international accolades",
        "evidence": ["link to performance", "award certificate"],
        "verification_contact": {
            "name": "Professor Music",
            "contact": "555-8765"
        }
    })

    # Support Team Collection
    support_teams = db['support_teams']
    support_teams.insert_one({
        "support_team_id": "support_team_1",
        "applicant_id": "applicant_1",
        "role": "interpreter",
        "first_name": "Alice",
        "last_name": "Smith",
        "title": "Certified Interpreter",
        "daytime_phone": "555-2345",
        "mobile_phone": "555-6789",
        "email": "alice.smith@example.com"
    })
    support_teams.insert_one({
        "support_team_id": "support_team_2",
        "applicant_id": "applicant_1",
        "role": "preparer",
        "first_name": "Bob",
        "last_name": "Johnson",
        "title": "Certified Preparer",
        "daytime_phone": "555-3456",
        "mobile_phone": "555-7890",
        "email": "bob.johnson@example.com"
    })
    support_teams.insert_one({
        "support_team_id": "support_team_3",
        "applicant_id": "applicant_1",
        "role": "lawyer",
        "first_name": "Charlie",
        "last_name": "Brown",
        "title": "Immigration Lawyer",
        "daytime_phone": "555-4567",
        "mobile_phone": "555-8901",
        "email": "charlie.brown@example.com"
    })
    
    # Services Collection
    services = db['services']
    services.insert_one({
        "service_id": "service_1",
        "applicant_id": "applicant_1",
        "form_name": "I-485",
        "status": "in_progress",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "preparer_id": "support_team_2",
        "interpreter_id": "support_team_1",
        "lawyer_id": "support_team_3",
        "sub_processes": [
            {
                "sub_process_id": "sub_process_1",
                "name": "FOIA request",
                "status": "pending",
                "start_date": "2023-01-05",
                "end_date": "2023-02-01"
            },
            {
                "sub_process_id": "sub_process_2",
                "name": "Criminal Background Check",
                "status": "completed",
                "start_date": "2023-01-10",
                "end_date": "2023-01-15"
            }
        ]
    })
    services.insert_one({
        "service_id": "service_2",
        "applicant_id": "applicant_1",
        "form_name": "I-130",
        "status": "completed",
        "start_date": "2022-01-01",
        "end_date": "2022-06-30",
        "preparer_id": "support_team_2",
        "interpreter_id": "support_team_1",
        "lawyer_id": "support_team_3",
        "sub_processes": [
            {
                "sub_process_id": "sub_process_3",
                "name": "Medical Background Check",
                "status": "completed",
                "start_date": "2022-01-05",
                "end_date": "2022-02-01"
            }
        ]
    })

    print("Data inserted successfully")

except errors.PyMongoError as e:
    print(f"An error occurred: {e}")