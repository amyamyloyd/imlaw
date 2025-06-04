# Persona Logic for USCIS Form Field Analysis

## 1. Persona Classification System

### Core Personas and Codes
```
APP: applicant           - Person filing the form
BEN: beneficiary        - Person benefiting from the application
FAM: family_member      - Family member of applicant (spouse, child, parent, sibling)
PRE: preparer           - Person helping fill out the form
ATT: attorney           - Attorney or accredited representative
INT: interpreter        - Person who translated for applicant
EMP: employer           - Current or prospective employer
PHY: physician          - Medical professional (for I-693)
SPO: sponsor            - Financial sponsor (for I-864)
```

## 2. Context Detection Patterns

### Applicant Patterns
- Direct mention: "applicant's"
- Self-reference: "your", "you are", "you have"
- Personal info: "information about you"

### Beneficiary Patterns
- Direct mention: "beneficiary's"
- Descriptive: "person for whom"
- Relationship: "relative you are sponsoring"
- Status: "foreign national"

### Family Member Patterns
- General: "family member's"
- Specific roles: "spouse's", "child's", "parent's", "sibling's"

### Preparer Patterns
- Direct mention: "preparer's"
- Role description: "person who prepared"
- Action context: "prepared this form/application"

### Attorney Patterns
- Direct terms: "attorney's", "lawyer's"
- Role description: "legal representative"
- Certification: "accredited representative"

### Interpreter Patterns
- Direct mention: "interpreter's"
- Role description: "person who interpreted"
- Action context: "translated for you"

### Employer Patterns
- Direct mention: "employer's"
- Organization types: "company's", "business's", "organization's"

### Physician Patterns
- Direct terms: "physician's", "doctor's"
- Role description: "medical examiner", "medical professional"
- Specific role: "civil surgeon"

### Sponsor Patterns
- Direct mention: "sponsor's"
- Role description: "person providing financial support"
- Specific role: "financial sponsor"

## 3. Multi-Source Context Analysis

The system analyzes persona context from multiple sources in the following order:

1. **Field Name Analysis**
   - Direct field identifier
   - Parent field name
   - Child field names
   - Field hierarchy context

2. **Tooltip Analysis**
   - Field's own tooltip
   - Parent field tooltip
   - Related field tooltips

3. **Form Section Context**
   - Section headers
   - Parent-child relationships
   - Field groupings

4. **Field Value Context**
   - Default values
   - Field type and format
   - Related field values

5. **Form-Specific Rules**
   - Known form sections
   - Standard field patterns
   - Form-specific conventions

## 4. Output and Review Process

### Automated Classification
- Fields with clear persona matches are classified automatically
- Multiple personas can be assigned if context indicates shared use
- Confidence scores are assigned to each persona match

### Manual Review Flags
Fields are flagged for manual review when:
- No clear persona context is found
- Conflicting persona indicators exist
- Novel patterns are detected
- Critical fields lack sufficient context

### Review Documentation
Generated files include:
1. Complete field listing with persona assignments
2. Fields needing manual review
3. Confidence scores for automated assignments
4. Context sources that led to each assignment

## 5. Continuous Improvement

The system supports ongoing refinement through:
1. Pattern Updates
   - New context patterns can be added
   - Existing patterns can be refined
   - Form-specific patterns can be defined

2. Review Feedback
   - Manual review results feed back into pattern matching
   - Common manual corrections inform pattern updates
   - Form-specific rules are updated based on review findings

3. Quality Metrics
   - Track automatic classification success rate
   - Monitor manual review requirements
   - Identify pattern effectiveness
   - Document form-specific challenges 