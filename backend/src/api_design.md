# ImLaw API Design

## Base URL
```
/api/v1
```

## Authentication
All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Authentication Endpoints

#### Login
```
POST /auth/login
```
- **Purpose**: Authenticate user and get access token
- **Body**: 
  - username: string
  - password: string
- **Response**: JWT token and user info

#### Refresh Token
```
POST /auth/refresh
```
- **Purpose**: Get new access token using refresh token
- **Body**: refresh_token: string
- **Response**: New JWT token

#### Logout
```
POST /auth/logout
```
- **Purpose**: Invalidate current token
- **Response**: Logout confirmation

## Endpoints

### Form Schemas

#### Get Form Schema
```
GET /form-schemas/{form_type}/{version}
```
- **Purpose**: Retrieve a specific form schema by type and version
- **Path Parameters**:
  - form_type: string (e.g., "i485", "i130")
  - version: string (e.g., "2024", "2023")
- **Response**: Form schema with fields, sections, and validation rules

#### List Form Schemas
```
GET /form-schemas
```
- **Purpose**: List all available form schemas
- **Query Parameters**:
  - form_type: string (optional, filter by type)
  - version: string (optional, filter by version)
  - active: boolean (optional, filter active/inactive)
  - page: integer (optional, for pagination)
  - limit: integer (optional, items per page)
- **Response**: 
  - items: Array of form schemas with metadata
  - total: Total number of items
  - page: Current page number
  - pages: Total number of pages

#### Create Form Schema
```
POST /form-schemas
```
- **Purpose**: Create a new form schema
- **Body**: Form schema definition including:
  - form_type: string
  - version: string
  - fields: Array of field definitions
  - sections: Array of section definitions
  - validation_rules: Array of validation rules
- **Response**: Created form schema with ID

#### Update Form Schema
```
PUT /form-schemas/{form_type}/{version}
```
- **Purpose**: Update an existing form schema
- **Path Parameters**: Same as GET
- **Body**: Updated form schema
- **Response**: Updated form schema

#### Delete Form Schema
```
DELETE /form-schemas/{form_type}/{version}
```
- **Purpose**: Mark a form schema as inactive
- **Path Parameters**: Same as GET
- **Response**: Deletion confirmation

### Client Data

#### Create Client Entry
```
POST /clients
```
- **Purpose**: Create a new client profile
- **Body**: Initial client data including:
  - email: string
  - first_name: string
  - last_name: string
  - phone: string (optional)
  - preferred_language: string (optional)
- **Response**: Created client profile with ID

#### Get Client Profile
```
GET /clients/{client_id}
```
- **Purpose**: Retrieve a client's complete profile
- **Path Parameters**:
  - client_id: string
- **Query Parameters**:
  - include_documents: boolean (optional, include document list)
  - include_progress: boolean (optional, include save progress)
- **Response**: Complete client profile with all sections

#### Update Client Profile
```
PUT /clients/{client_id}
```
- **Purpose**: Update a client's profile
- **Path Parameters**: Same as GET
- **Body**: Updated profile data
- **Response**: Updated client profile

#### Delete Client Profile
```
DELETE /clients/{client_id}
```
- **Purpose**: Mark a client profile as inactive
- **Path Parameters**: Same as GET
- **Response**: Deletion confirmation

#### Save Progress
```
POST /clients/{client_id}/progress
```
- **Purpose**: Save partial progress for a client
- **Path Parameters**: Same as GET
- **Body**: 
  - section: string (current section)
  - field: string (current field)
  - data: object (section/field data)
  - validation_errors: array (optional, validation issues)
- **Response**: 
  - save_status: string
  - completion_percentage: number
  - validation_errors: array

#### Get Save Progress
```
GET /clients/{client_id}/progress
```
- **Purpose**: Get current progress and validation state
- **Path Parameters**: Same as GET
- **Response**:
  - last_section: string
  - last_field: string
  - completion_percentage: number
  - validation_errors: array

### Repeatable Sections

#### Add Section
```
POST /clients/{client_id}/sections/{section_type}
```
- **Purpose**: Add a new repeatable section
- **Path Parameters**:
  - client_id: string
  - section_type: string (e.g., "address", "employment")
- **Body**: Section data
- **Response**: Added section with ID

#### Update Section
```
PUT /clients/{client_id}/sections/{section_type}/{section_id}
```
- **Purpose**: Update a specific section
- **Path Parameters**: Same as POST plus section_id
- **Body**: Updated section data
- **Response**: Updated section

#### Delete Section
```
DELETE /clients/{client_id}/sections/{section_type}/{section_id}
```
- **Purpose**: Remove a specific section
- **Path Parameters**: Same as PUT
- **Response**: Deletion confirmation

#### Reorder Sections
```
PUT /clients/{client_id}/sections/{section_type}/order
```
- **Purpose**: Reorder sections of a specific type
- **Path Parameters**: Same as POST
- **Body**: Array of section IDs in new order
- **Response**: Updated order confirmation

### Document Management

#### Upload Document
```
POST /clients/{client_id}/documents
```
- **Purpose**: Upload a new document
- **Path Parameters**:
  - client_id: string
- **Body**: Multipart form with file and metadata
- **Response**: Upload confirmation with document ID

#### Update Document Status
```
PUT /clients/{client_id}/documents/{document_id}/status
```
- **Purpose**: Update document status (approve/reject)
- **Path Parameters**:
  - client_id: string
  - document_id: string
- **Body**: New status and reason
- **Response**: Updated document status

#### Get Documents
```
GET /clients/{client_id}/documents
```
- **Purpose**: List all client documents
- **Path Parameters**:
  - client_id: string
- **Query Parameters**:
  - status: string (optional, filter by status)
  - type: string (optional, filter by document type)
- **Response**: Array of documents with metadata

### Canonical Fields

#### Get Canonical Fields
```
GET /canonical-fields
```
- **Purpose**: List all canonical fields
- **Query Parameters**:
  - category: string (optional, filter by category)
  - search: string (optional, search term)
- **Response**: Array of canonical fields

#### Create Canonical Field
```
POST /canonical-fields
```
- **Purpose**: Create a new canonical field
- **Body**: Field definition
- **Response**: Created canonical field

#### Update Canonical Field
```
PUT /canonical-fields/{field_id}
```
- **Purpose**: Update a canonical field
- **Path Parameters**:
  - field_id: string
- **Body**: Updated field definition
- **Response**: Updated canonical field

### Field Mappings

#### Get Field Mappings
```
GET /field-mappings
```
- **Purpose**: List all field mappings
- **Query Parameters**:
  - form_type: string (optional, filter by form type)
  - canonical_field: string (optional, filter by canonical field)
- **Response**: Array of field mappings

#### Create Field Mapping
```
POST /field-mappings
```
- **Purpose**: Create a new field mapping
- **Body**: Mapping definition
- **Response**: Created field mapping

#### Update Field Mapping
```
PUT /field-mappings/{mapping_id}
```
- **Purpose**: Update a field mapping
- **Path Parameters**:
  - mapping_id: string
- **Body**: Updated mapping
- **Response**: Updated field mapping

### Version Control

#### Get Active Version
```
GET /versions/{form_type}/active
```
- **Purpose**: Get currently active version for a form type
- **Path Parameters**:
  - form_type: string
- **Response**: Active version details

#### Compare Versions
```
GET /versions/{form_type}/compare
```
- **Purpose**: Compare two versions of a form
- **Path Parameters**:
  - form_type: string
- **Query Parameters**:
  - v1: string (first version)
  - v2: string (second version)
- **Response**: Version differences

#### Activate Version
```
POST /versions/{form_type}/{version}/activate
```
- **Purpose**: Make a version active
- **Path Parameters**:
  - form_type: string
  - version: string
- **Response**: Activation confirmation

## Error Responses

All endpoints follow a consistent error response format:
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {
      "field": "error description",
      "additional_info": {}
    }
  }
}
```

Common HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 429: Too Many Requests
- 500: Internal Server Error

## Rate Limiting

All endpoints are rate-limited based on the authenticated user:
- Standard users: 100 requests per minute
- Admin users: 1000 requests per minute
- Unauthenticated: 20 requests per minute

Rate limit headers included in responses:
```
X-RateLimit-Limit: <requests_per_minute>
X-RateLimit-Remaining: <requests_remaining>
X-RateLimit-Reset: <reset_timestamp>
```

## Versioning

The API uses URL versioning (v1) to ensure backward compatibility. Breaking changes will result in a new version number.

## CORS

The API supports Cross-Origin Resource Sharing (CORS) with the following defaults:
- Allowed Origins: Configured per environment
- Allowed Methods: GET, POST, PUT, DELETE, OPTIONS
- Allowed Headers: Content-Type, Authorization
- Max Age: 86400 seconds (24 hours)

## Caching

Responses include appropriate cache control headers:
- GET requests: Cache-Control: private, max-age=3600
- POST/PUT/DELETE: Cache-Control: no-store
- Error responses: Cache-Control: no-store 