import os
import csv
from dotenv import load_dotenv
from jira import JIRA

# Load environment variables from the .env file
load_dotenv()

# Retrieve the values of the environment variables
jira_url = os.getenv('JIRA_URL')
username = os.getenv('JIRA_USERNAME')
token = os.getenv('JIRA_API_TOKEN')

# Connect to Jira using the environment variables
jira = JIRA(server=jira_url, basic_auth=(username, token))

# Specify the issue key and subtask key
issue_key = 'CF-1'  # Replace with the issue key you want to retrieve
subtask_key = 'CF-6'  # Replace with the subtask key(s)

# Fetch all fields for the Jira instance (this provides the field names)
fields = jira.fields()

# Create a dictionary for field names by field ID
field_dict = {field['id']: field['name'] for field in fields}

# Fetch the issue using the JIRA API
issue = jira.issue(issue_key)

# Create and write to the CSV file
with open('jira_fields_output.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    
    # Write the header
    writer.writerow(['Field Name', 'Field ID', 'Field Value'])

    # Write the fields and their values for the issue
    for field_id, field_value in issue.fields.__dict__.items():
        field_name = field_dict.get(field_id, field_id)  # Get the field name using the field ID
        writer.writerow([field_name, field_id, field_value])

    # Fetch the subtask using the JIRA API
    subtask = jira.issue(subtask_key)

    # Write the fields and their values for the subtask
    for subtask_field_id, subtask_field_value in subtask.fields.__dict__.items():
        subtask_field_name = field_dict.get(subtask_field_id, subtask_field_id)  # Get the field name using the field ID
        writer.writerow([subtask_field_name, subtask_field_id, subtask_field_value])

print("CSV file 'jira_fields_output.csv' has been created successfully!")
