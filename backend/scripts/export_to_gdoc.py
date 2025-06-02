"""
Script to export field tooltips table to a Google Doc.
Requires the Google Drive API credentials to be set up.
"""

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import os

def create_google_doc():
    # Path to your service account credentials JSON file
    CREDENTIALS_FILE = 'credentials.json'
    
    try:
        # Initialize credentials
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/documents', 
                   'https://www.googleapis.com/auth/drive.file']
        )
        
        # Create Google Docs service
        docs_service = build('docs', 'v1', credentials=credentials)
        
        # Create a new document
        document = {
            'title': 'Immigration Form Fields Analysis'
        }
        doc = docs_service.documents().create(body=document).execute()
        doc_id = doc.get('documentId')
        
        print(f'Created document with ID: {doc_id}')
        
        # Read the field tooltips data
        with open('/Users/claudiapitts/imlaw/Imlaw/generalscripts/field_analysis/field_tooltips.txt', 'r') as f:
            content = f.read()
        
        # Prepare the content for Google Docs
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1
                    },
                    'text': content
                }
            },
            # Add formatting for the header
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': content.find('\n')
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_1'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ]
        
        # Apply the changes to the document
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        print(f'\nDocument created successfully!')
        print(f'View your document at: https://docs.google.com/document/d/{doc_id}/edit')
        
    except HttpError as error:
        print(f'An error occurred: {error}')
        
if __name__ == '__main__':
    create_google_doc() 