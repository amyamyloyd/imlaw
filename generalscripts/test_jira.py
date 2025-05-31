import os
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

# Test the connection by retrieving the authenticated user's details
user = jira.myself()

# Print the user's display name to verify the connection
print(f"Connected to Jira as {user['displayName']}")
