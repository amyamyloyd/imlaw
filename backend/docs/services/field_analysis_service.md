# Field Analysis Service Documentation

## Overview
The Field Analysis Service is a collection of Python scripts that analyze immigration form PDFs to extract, normalize, and analyze form fields. The service handles forms like i485, i130, i693, and i765, extracting field metadata, relationships, and patterns.

## Core Scripts

### 1. analyze_form_fields.py
**Purpose**: Primary PDF analysis script that extracts raw field data and metadata from immigration PDFs.

**Key Functions**:
- `FormFieldAnalyzer.analyze_form()`: Analyzes a single PDF form
- `FormFieldAnalyzer.analyze_all_forms()`: Processes all target forms
- `FormFieldAnalyzer.extract_field_data()`: Extracts detailed field metadata
- `FormFieldAnalyzer.extract_document_metadata()`: Gets PDF-level metadata
- `FormFieldAnalyzer.extract_page_data()`: Extracts page-specific information

**Outputs**:
- `complete_analysis.json`: Full analysis of all forms
- `all_fields_listing.csv`: Consolidated field listing
- `field_relationships.json`: Parent-child field relationships
- Per-form JSON files (e.g., `i485_fields.json`)

**Generated Metadata**:
- Field properties (name, type, page, flags)
- Field relationships (parent-child hierarchies)
- Field attributes (readonly, required)
- Page resources (fonts, images)
- Document metadata
- Field tooltips and annotations

### 2. export_fields.py
**Purpose**: Converts and normalizes field data from CSV format to structured JSON.

**Key Functions**:
- `normalize_field_type()`: Standardizes field types
- `extract_form_id()`: Extracts standardized form identifiers
- `convert_fields_to_json()`: Converts CSV data to structured JSON

**Outputs**:
- `extracted_fields.json`: Normalized field data with:
  - Form ID
  - Field name
  - Normalized type
  - Tooltip
  - Base type
  - Page number
  - Field rules
  - Keywords

### 3. analyze_field_patterns.py
**Purpose**: Analyzes field patterns, relationships, and generates comprehensive reports.

**Key Functions**:
- Pattern detection for reused fields
- Field categorization
- Domain analysis
- Persona mapping
- Biographical data analysis

**Outputs**:
- Analysis results directory with timestamp
- Field analysis results (JSON/CSV)
- Analysis tables (text)
- Domain analysis
- Metadata summary

## Rule Definitions

### Location of Rules
Rules are stored in several key files:

1. **Field Rules**: `/backend/field_analysis/field_rules.json`
   - Pattern definitions
   - Domain rules
   - Persona definitions
   - Biographical subcategories

2. **Field Mappings**: `/backend/field_analysis/field_mappings.json`
   - Type mappings
   - Field standardization rules
   - Relationship definitions

### Rule Categories

1. **Pattern Rules**:
   - Reused field patterns (e.g., contact info, personal info)
   - Repeating field patterns (e.g., children, employment history)
   - Detection rules for pattern matching

2. **Domain Rules**:
   - Field domain categorization
   - Confidence scoring
   - Pattern matching rules

3. **Persona Rules**:
   - Applicant
   - Preparer
   - Family member
   - Employer
   - Reference

4. **Biographical Rules**:
   - Personal characteristics
   - Contact information
   - Document information
   - Employment history
   - Family relationships

## Output Directory Structure

```
field_analysis/
├── analysis_results_[TIMESTAMP]/
│   ├── field_analysis_results_[TIMESTAMP].csv
│   ├── field_analysis_results_[TIMESTAMP].json
│   ├── field_analysis_table_[TIMESTAMP].txt
│   ├── domain_analysis_table_[TIMESTAMP].txt
│   └── analysis_metadata_[TIMESTAMP].json
├── extracted_fields.json
├── field_rules.json
├── field_mappings.json
└── [form]_fields.json
```

## Service Integration Guidelines

### Adding New Forms

1. Place new PDF in forms directory
2. Update `target_forms` in `FormFieldAnalyzer`
3. Run `analyze_form_fields.py`
4. Verify field extraction in output files
5. Update rules if needed for new patterns

### Updating Rules

1. Analyze new patterns in form fields
2. Update relevant rule files:
   - Add new patterns to field_rules.json
   - Update mappings in field_mappings.json
3. Run analysis to verify rule changes
4. Document new rules and patterns

### Processing Pipeline

1. **Form Analysis**:
   ```python
   analyzer = FormFieldAnalyzer()
   analyzer.analyze_all_forms()
   ```

2. **Field Export**:
   ```python
   python export_fields.py
   ```

3. **Pattern Analysis**:
   ```python
   python analyze_field_patterns.py
   ```

## Common Field Patterns

1. **Reused Fields**:
   - Contact information (43 instances)
   - Personal information (205 instances)
   - Preparer information (2 instances)

2. **Repeating Fields**:
   - Children information (sequences 1-3)
   - Employment history (sequences 1-2)
   - Family relationships (sequences 1-2)

3. **Field Types**:
   - Text fields: 1031
   - Buttons: 652
   - Checkboxes: 42

## Future Enhancements

1. **Automated Rule Generation**:
   - Pattern detection for new forms
   - Rule suggestion system
   - Confidence scoring for new patterns

2. **API Integration**:
   - REST endpoints for analysis
   - Webhook notifications
   - Real-time processing

3. **Validation Enhancement**:
   - Cross-form field validation
   - Rule conflict detection
   - Pattern optimization

4. **Reporting Improvements**:
   - Interactive visualizations
   - Pattern relationship graphs
   - Change tracking between versions 