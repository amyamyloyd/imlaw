# Admin UI Components Documentation

## 1. Component Structure

### Main Components

#### CanonicalFieldsAdmin (pages/admin/CanonicalFieldsAdmin.tsx)
- Main container component managing state and API interactions
- Handles CRUD operations for canonical fields
- Manages dialog windows for forms and mapping
- Provides feedback through snackbar notifications

#### CanonicalFieldList (components/admin/CanonicalFieldList.tsx)
- Displays canonical fields in a paginated table
- Provides search and filtering by category/data type
- Supports add/edit/delete operations
- Shows field usage statistics and mapping counts

#### CanonicalFieldForm (components/admin/CanonicalFieldForm.tsx)
- Form for creating/editing canonical fields
- Manages field properties including name, type, category
- Handles validation rules through a dialog interface
- Supports alias management with add/remove functionality

#### FieldMappingManager (components/admin/FieldMappingManager.tsx)
- Manages form field mappings for a canonical field
- Shows existing mappings in a table view
- Provides interface for adding new mappings
- Displays and allows accepting mapping suggestions
- Supports different mapping types (direct/transform/composite)

## 2. Features Implemented

### Canonical Field Management
- Create, read, update, delete operations
- Field properties:
  - Basic info (name, display name, description)
  - Data type selection
  - Category assignment
  - Required field toggle
  - Aliases management
  - Validation rules

### Field Mapping Features
- View existing mappings
- Add new mappings with form type/version selection
- Remove mappings
- Support for different mapping types
- Transform logic for non-direct mappings
- Mapping suggestions with confidence scores

### UI/UX Features
- Material-UI based design
- Responsive layout
- Search and filtering capabilities
- Pagination for large datasets
- Dialog-based forms
- Success/error notifications
- Loading states
- Tooltips and helpful messages

## 3. Data Types and Interfaces

Created comprehensive TypeScript interfaces in `canonical-field.ts`:
- `DataType` enum for field types
- `ValidationRule` interface for field validation
- `ValidationHistory` for tracking changes
- `UsageStats` for field usage metrics
- `FormFieldMapping` for form field relationships
- `CanonicalField` as the main data structure

## 4. API Integration

Implemented API endpoints integration for:
- CRUD operations on canonical fields
- Field mapping management
- Mapping suggestions
- Available forms fetching

## 5. Navigation

Set up React Router with:
- Home page route
- Canonical fields admin route
- Navigation header with links

This implementation provides a complete administrative interface for managing the canonical field registry, supporting all the required functionality while maintaining a clean and intuitive user experience. 