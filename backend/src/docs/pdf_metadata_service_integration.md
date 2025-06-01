# PDF Metadata Service Integration Guide

## Overview

The PDF Metadata Service is a form-agnostic solution for extracting, storing, and managing metadata from PDF forms. This service provides a RESTful API that enables other services to:

- Extract metadata from PDF forms
- Store and retrieve field definitions
- Manage form versions
- Map fields to canonical names
- Access form metadata efficiently

## Quick Start

### Base URL
```
http://your-domain/api/v1/pdf-metadata
```

### Authentication
All requests must include an API key in the header:
```
Authorization: Bearer your-api-key
```

## API Endpoints

### 1. Upload and Extract Metadata

**Endpoint:** `POST /extract`

Upload a PDF and extract its metadata:

```python
import requests

url = "http://your-domain/api/v1/pdf-metadata/extract"
files = {"file": ("form.pdf", open("form.pdf", "rb"))}
headers = {"Authorization": "Bearer your-api-key"}
params = {"form_type": "i485"}  # Optional form type identifier

response = requests.post(url, files=files, headers=headers, params=params)
metadata = response.json()
```

**Response:**
```json
{
  "form_id": "12345",
  "title": "Form I-485",
  "pages": 18,
  "fields": [
    {
      "field_id": "name_first",
      "field_type": "Tx",
      "field_name": "First Name",
      "tooltip": "Enter your legal first name",
      "position": {
        "x": 10,
        "y": 20,
        "width": 100,
        "height": 20
      }
    }
  ]
}
```

### 2. Retrieve Form Metadata

**Endpoint:** `GET /forms/{form_id}`

Get metadata for a specific form:

```python
import requests

url = f"http://your-domain/api/v1/pdf-metadata/forms/{form_id}"
headers = {"Authorization": "Bearer your-api-key"}

response = requests.get(url, headers=headers)
form = response.json()
```

### 3. Get Form Fields

**Endpoint:** `GET /forms/{form_id}/fields`

Retrieve field definitions for a form:

```python
import requests

url = f"http://your-domain/api/v1/pdf-metadata/forms/{form_id}/fields"
headers = {"Authorization": "Bearer your-api-key"}

response = requests.get(url, headers=headers)
fields = response.json()
```

### 4. Update Field Definitions

**Endpoint:** `PUT /forms/{form_id}/fields`

Update field definitions for a form:

```python
import requests

url = f"http://your-domain/api/v1/pdf-metadata/forms/{form_id}/fields"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}
data = {
    "fields": [
        {
            "field_id": "name_first",
            "field_type": "Tx",
            "field_name": "First Name",
            "required": True
        }
    ]
}

response = requests.put(url, json=data, headers=headers)
```

### 5. Delete Form

**Endpoint:** `DELETE /forms/{form_id}`

Delete a form and its metadata:

```python
import requests

url = f"http://your-domain/api/v1/pdf-metadata/forms/{form_id}"
headers = {"Authorization": "Bearer your-api-key"}

response = requests.delete(url, headers=headers)
```

## Error Handling

The service uses standard HTTP status codes:

- 200: Success
- 400: Bad Request (invalid input)
- 401: Unauthorized (invalid API key)
- 404: Not Found
- 500: Internal Server Error

Error responses include detailed messages:

```json
{
  "error": {
    "code": "INVALID_FIELD_TYPE",
    "message": "Invalid field type specified",
    "details": {
      "field_id": "name_first",
      "invalid_type": "invalid_type"
    }
  }
}
```

## Best Practices

1. **Caching**
   - Cache form metadata and field definitions
   - Use ETags for cache validation
   - Implement conditional requests

2. **Rate Limiting**
   - Respect rate limits (100 requests/minute)
   - Implement exponential backoff for retries

3. **Error Handling**
   - Implement proper error handling
   - Log failed requests for debugging
   - Use appropriate timeout values

4. **Security**
   - Keep API keys secure
   - Use HTTPS for all requests
   - Validate input data

## MongoDB Schema

The service uses the following MongoDB schema for storing form metadata:

```javascript
{
  _id: ObjectId,
  title: String,
  description: String,
  pages: Number,
  created_at: ISODate,
  updated_at: ISODate,
  fields: [{
    field_id: String,
    field_type: String,
    field_name: String,
    field_value: Mixed,
    position: {
      x: Number,
      y: Number,
      width: Number,
      height: Number
    },
    properties: Mixed
  }]
}
```

## Integration Examples

### Example 1: Basic Form Processing

```python
import requests

def process_form(pdf_path, form_type):
    # 1. Upload and extract metadata
    with open(pdf_path, "rb") as pdf:
        metadata = upload_and_extract(pdf, form_type)
    
    # 2. Get field definitions
    fields = get_field_definitions(metadata["form_id"])
    
    # 3. Process fields as needed
    for field in fields:
        process_field(field)

def upload_and_extract(pdf_file, form_type):
    url = "http://your-domain/api/v1/pdf-metadata/extract"
    files = {"file": pdf_file}
    params = {"form_type": form_type}
    headers = {"Authorization": "Bearer your-api-key"}
    
    response = requests.post(url, files=files, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

def get_field_definitions(form_id):
    url = f"http://your-domain/api/v1/pdf-metadata/forms/{form_id}/fields"
    headers = {"Authorization": "Bearer your-api-key"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def process_field(field):
    # Process each field based on your requirements
    print(f"Processing field: {field['field_name']}")
```

### Example 2: Batch Processing with Error Handling

```python
import requests
from typing import List, Dict
import time

class PDFMetadataClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.session = requests.Session()
    
    def process_batch(self, pdfs: List[Dict[str, str]], max_retries: int = 3):
        results = []
        for pdf in pdfs:
            retry_count = 0
            while retry_count < max_retries:
                try:
                    # Extract metadata
                    metadata = self._extract_metadata(pdf["path"], pdf["type"])
                    
                    # Get fields
                    fields = self._get_fields(metadata["form_id"])
                    
                    results.append({
                        "pdf": pdf["path"],
                        "metadata": metadata,
                        "fields": fields
                    })
                    break
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        results.append({
                            "pdf": pdf["path"],
                            "error": str(e)
                        })
                    time.sleep(2 ** retry_count)  # Exponential backoff
        
        return results
    
    def _extract_metadata(self, pdf_path: str, form_type: str):
        url = f"{self.base_url}/extract"
        with open(pdf_path, "rb") as pdf:
            response = self.session.post(
                url,
                files={"file": pdf},
                params={"form_type": form_type},
                headers=self.headers
            )
        response.raise_for_status()
        return response.json()
    
    def _get_fields(self, form_id: str):
        url = f"{self.base_url}/forms/{form_id}/fields"
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

# Usage example
client = PDFMetadataClient(
    "http://your-domain/api/v1/pdf-metadata",
    "your-api-key"
)

pdfs = [
    {"path": "form1.pdf", "type": "i485"},
    {"path": "form2.pdf", "type": "i130"}
]

results = client.process_batch(pdfs)
```

## Common Integration Patterns

### 1. Form Processing Pipeline

```python
from typing import Dict, Any
import requests

class FormProcessor:
    def __init__(self, metadata_service_url: str, api_key: str):
        self.metadata_service_url = metadata_service_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def process_form(self, pdf_path: str, form_type: str) -> Dict[str, Any]:
        # 1. Extract metadata
        metadata = self.extract_metadata(pdf_path, form_type)
        
        # 2. Validate form type
        self.validate_form_type(metadata)
        
        # 3. Get field definitions
        fields = self.get_field_definitions(metadata["form_id"])
        
        # 4. Process fields
        processed_fields = self.process_fields(fields)
        
        return {
            "metadata": metadata,
            "processed_fields": processed_fields
        }
    
    def extract_metadata(self, pdf_path: str, form_type: str) -> Dict[str, Any]:
        url = f"{self.metadata_service_url}/extract"
        with open(pdf_path, "rb") as pdf:
            response = requests.post(
                url,
                files={"file": pdf},
                params={"form_type": form_type},
                headers=self.headers
            )
        response.raise_for_status()
        return response.json()
    
    def validate_form_type(self, metadata: Dict[str, Any]) -> None:
        # Add your form type validation logic
        pass
    
    def get_field_definitions(self, form_id: str) -> Dict[str, Any]:
        url = f"{self.metadata_service_url}/forms/{form_id}/fields"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def process_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        # Add your field processing logic
        return fields
```

### 2. Caching Integration

```python
from functools import lru_cache
import requests
import time
from typing import Dict, Any

class CachedMetadataClient:
    def __init__(self, base_url: str, api_key: str, cache_ttl: int = 3600):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.cache_ttl = cache_ttl
    
    @lru_cache(maxsize=100)
    def get_form_metadata(self, form_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/forms/{form_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_form_fields(self, form_id: str) -> Dict[str, Any]:
        # Use cache with timestamp validation
        cache_key = f"fields_{form_id}"
        cached_data = self._get_cache(cache_key)
        
        if cached_data and time.time() - cached_data["timestamp"] < self.cache_ttl:
            return cached_data["data"]
        
        url = f"{self.base_url}/forms/{form_id}/fields"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        
        self._set_cache(cache_key, data)
        return data
    
    def _get_cache(self, key: str) -> Dict[str, Any]:
        # Implement your caching logic here
        pass
    
    def _set_cache(self, key: str, data: Dict[str, Any]) -> None:
        # Implement your caching logic here
        pass
```

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Errors**
   - Verify API key is valid and not expired
   - Check if API key has correct permissions
   - Ensure key is properly formatted in header

2. **Rate Limiting**
   - Implement exponential backoff
   - Use bulk operations where possible
   - Cache frequently accessed data

3. **Performance Issues**
   - Use appropriate indexes
   - Implement caching
   - Optimize query patterns

4. **Data Validation Errors**
   - Validate input before sending
   - Check field types match schema
   - Verify required fields are present

## Support

For additional support:
- Email: support@your-domain.com
- Documentation: https://your-domain.com/docs
- API Status: https://status.your-domain.com 