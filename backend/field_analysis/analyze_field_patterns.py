import json
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from tabulate import tabulate
from datetime import datetime
from collections import defaultdict
import numpy as np

class FieldAnalyzer:
    def __init__(self, rules_file: str, mapping_file: str):
        """Initialize with rules and mapping configurations."""
        with open(rules_file, 'r') as f:
            self.rules = json.load(f)
        with open(mapping_file, 'r') as f:
            self.mappings = json.load(f)
        
        # Extract reused and repeating patterns from rules
        self.reused_patterns = self._extract_reused_patterns()
        self.repeating_patterns = self._extract_repeating_patterns()
        
        # Keep existing persona and biographical definitions
        self.personas = self.rules.get("personas", {})
        self.biographical_subcategories = self.rules.get("biographical_subcategories", {})
        self.domain_indicators = self.rules.get("domain_indicators", {})

    def _extract_reused_patterns(self) -> Dict:
        """Extract reused field patterns from rules."""
        reused = self.rules["rule_types"]["reused"]
        patterns = {
            "detection": reused["detection_rules"],
            "categories": {}
        }
        
        for cat_name, cat_data in reused.get("categories", {}).items():
            patterns["categories"][cat_name] = {
                "indicators": cat_data["indicators"],
                "collection": cat_data["collection"],
                "mapping": cat_data["mapping"]
            }
        
        return patterns

    def _extract_repeating_patterns(self) -> Dict:
        """Extract repeating field patterns from rules."""
        repeating = self.rules["rule_types"]["repeating"]
        patterns = {
            "detection": repeating["detection_rules"],
            "categories": {}
        }
        
        for cat_name, cat_data in repeating.get("categories", {}).items():
            patterns["categories"][cat_name] = {
                "pattern": cat_data["pattern"],
                "collection": cat_data["collection"],
                "mapping": cat_data["mapping"],
                "indicators": cat_data["indicators"]
            }
        
        return patterns

    def parse_field_name(self, field_name: str) -> Dict:
        """Parse field name using multiple patterns to handle different formats.
        
        Handles patterns like:
        - P4Line5a_FamilyName[0]
        - P5_Line6a_SignatureofApplicant[0]
        - PDF417BarCode1[0]
        - Part4Line1_No[0]
        - Pt1Line3_Yes[0]
        - Pt1Line1_Parent[0]
        - AttorneyStateBarNumber[0]
        - Checkbox1234[0]
        """
        result = {
            "part": None,
            "part_num": None,
            "line": None,
            "subline": None,
            "field_type": None,
            "position": None
        }
        
        # Extract position if present (common across all patterns)
        position_match = re.search(r'\[(\d+)\]$', field_name)
        if position_match:
            result["position"] = position_match.group(1)
            # Remove position for further processing
            field_name = field_name[:position_match.start()]
        
        # Pattern 1: Checkbox fields (e.g., Checkbox1234)
        if field_name.startswith('Checkbox'):
            checkbox_match = re.match(r'Checkbox(\d+)', field_name)
            if checkbox_match:
                result["field_type"] = "Checkbox"
                result["part_num"] = checkbox_match.group(1)
                return result
        
        # Pattern 2: Attorney State Bar Number
        if field_name.startswith('AttorneyStateBarNumber'):
            result["field_type"] = "AttorneyStateBarNumber"
            result["part"] = "Office"
            return result
        
        # Pattern 3: Barcode fields (e.g., PDF417BarCode1)
        if field_name.startswith('PDF417'):
            barcode_match = re.match(r'PDF417BarCode(\d+)', field_name)
            if barcode_match:
                result["field_type"] = "BarCode"
                result["part_num"] = barcode_match.group(1)
                result["part"] = f"BarCode {barcode_match.group(1)}"
                return result
        
        # Extract part number first - handles Part4, P4, Pt4 formats
        part_patterns = [
            r'^Part(\d+)',  # Part4
            r'^P(?:art)?(\d+)',  # P4 or Part4
            r'^Pt(\d+)'  # Pt4
        ]
        
        for pattern in part_patterns:
            part_match = re.match(pattern, field_name)
            if part_match:
                part_num = part_match.group(1)
                result["part_num"] = part_num
                result["part"] = f"Part {part_num}"
                break
        
        # Pattern 4: Line number with optional subline and field type
        line_pattern = r'Line(\d+)([a-z])?(?:_(.+))?$'
        line_match = re.search(line_pattern, field_name)
        
        if line_match:
            line_num, subline, field_type = line_match.groups()
            result.update({
                "line": f"Line {line_num}",
                "subline": subline
            })
            
            if field_type:
                # Handle Yes/No fields
                if field_type.lower() in ['yes', 'no']:
                    result["field_type"] = field_type.capitalize()
                else:
                    result["field_type"] = field_type
        
        # If no field type was set but we have the original name
        if not result["field_type"]:
            result["field_type"] = field_name
        
        return result

    def analyze_domain(self, tooltip: str) -> List[Tuple[str, float]]:
        """Analyze tooltip to determine domain categories."""
        matches = []
        tooltip_lower = tooltip.lower()
        
        # Apply domain rules
        for domain, rules in self.rules["domains"].items():
            for rule in rules:
                if any(pattern.lower() in tooltip_lower for pattern in rule["patterns"]):
                    matches.append((domain, rule["confidence"]))
                    break  # Stop after first match for this domain
        
        return matches if matches else [("unknown", 0.0)]

    def analyze_tooltip(self, tooltip: str) -> List[Tuple[str, float, str]]:
        """Analyze tooltip text against rule patterns and return matching rules with confidence scores."""
        matches = []
        
        # Convert tooltip to lowercase for matching
        tooltip_lower = tooltip.lower()
        
        for rule_name, rule_data in self.rules["rule_types"].items():
            confidence = 0
            match_reasons = []
            
            # Check categories and their indicators
            if "categories" in rule_data:
                for cat_name, cat_data in rule_data["categories"].items():
                    if "indicators" in cat_data:
                        for indicator in cat_data["indicators"]:
                            if indicator.lower() in tooltip_lower:
                                confidence += 0.3
                                match_reasons.append(f"Found indicator '{indicator}' in category '{cat_name}'")
            
            # Check base types from field_mapping.json
            field_type_match = False
            for field_type, type_data in self.mappings["field_types"].items():
                if "rules" in type_data and rule_name in type_data["rules"]:
                    field_type_match = True
                    confidence += 0.2
                    match_reasons.append(f"Matches field type '{field_type}'")
            
            # If we found any matches, add to results
            if confidence > 0:
                matches.append((rule_name, confidence, "; ".join(match_reasons)))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)

    def analyze_persona(self, tooltip: str, field_name: str) -> List[Tuple[str, float]]:
        """Analyze tooltip and field name to determine persona."""
        matches = []
        text_lower = (tooltip + " " + field_name).lower()
        
        # Check each persona's indicators
        for persona, info in self.personas.items():
            if any(indicator.lower() in text_lower for indicator in info["indicators"]):
                matches.append((persona, info["confidence"]))
        
        return matches if matches else [("unknown", 0.0)]

    def analyze_biographical_subcategory(self, tooltip: str, field_name: str) -> List[Tuple[str, float]]:
        """Analyze tooltip to determine biographical subcategories."""
        matches = []
        text_lower = (tooltip + " " + field_name).lower()
        
        # Check each subcategory's patterns
        for subcat, rules in self.rules["biographical_subcategories"].items():
            for rule in rules:
                if any(pattern.lower() in text_lower for pattern in rule["patterns"]):
                    matches.append((subcat, rule["confidence"]))
                    break  # Stop after first match for this subcategory
        
        return matches if matches else [("unknown", 0.0)]

    def analyze_field(self, field_name: str, tooltip: str, field_type: str, form_id: str = None) -> Dict:
        """Analyze a single field and return its properties."""
        # Parse field name components
        parsed = self.parse_field_name(field_name)
        
        # Initialize result
        result = {
            "field_name": field_name,
            "tooltip": tooltip,
            "field_type": field_type,
            "form_id": form_id,  # Store the source form ID
            "needs_review": False,
            "confidence": 0.0,
            "domains": [],
            "personas": [],
            "biographical_subcategories": [],
            "is_reused": False,
            "reuse_category": None,
            "is_repeating": False,
            "repeating_category": None,
            "sequence_number": None,
            "mapping_type": None
        }
        result.update(parsed)  # Add parsed field name components
        
        # Check for reused fields
        reused_analysis = self.analyze_reused_field(tooltip, field_name)
        if reused_analysis["is_reused"]:
            result.update(reused_analysis)
        
        # Check for repeating fields
        repeating_analysis = self.analyze_repeating_field(tooltip, field_name)
        if repeating_analysis["is_repeating"]:
            result.update(repeating_analysis)
        
        # Special handling for Checkbox fields
        if field_name.startswith('Checkbox'):
            if tooltip:
                select_match = re.search(r'Select this box (.+?)\.', tooltip)
                if select_match:
                    result["base_field_type"] = select_match.group(1).strip()
                else:
                    sentences = re.split(r'[.!?]+', tooltip)
                    if sentences:
                        result["base_field_type"] = sentences[-1].strip()
        
        # Special handling for AttorneyStateBarNumber
        if field_name.startswith('AttorneyStateBarNumber'):
            result["domains"] = [("office", 2.0)]
            result["personas"] = [("preparer", 2.0)]
            result["confidence"] = 2.0
            result["is_reused"] = True
            result["reuse_category"] = "preparer_info"
        
        # Apply domain rules if not already set
        if not result["domains"]:
            result["domains"] = self.analyze_domain(tooltip)
        
        # Apply persona rules if not already set
        if not result["personas"]:
            result["personas"] = self.analyze_persona(tooltip, field_name)
        
        # Apply biographical subcategory rules
        if not result["biographical_subcategories"]:
            result["biographical_subcategories"] = self.analyze_biographical_subcategory(tooltip, field_name)
        
        # Calculate overall confidence
        if not result["confidence"]:
            confidences = [conf for _, conf in result["domains"]]
            result["confidence"] = max(confidences) if confidences else 0.0
        
        return result

    def analyze_reused_field(self, tooltip: str, field_name: str) -> Dict:
        """Analyze if a field is reused across the form."""
        result = {
            "is_reused": False,
            "reuse_category": None,
            "mapping_type": None
        }
        
        # Check for prepopulate pattern
        if "prepopulate from page" in tooltip.lower():
            result["is_reused"] = True
            result["mapping_type"] = "prepopulate"
            return result
        
        # Check categories
        tooltip_lower = tooltip.lower()
        field_name_lower = field_name.lower()
        
        for category, data in self.reused_patterns["categories"].items():
            if any(indicator in tooltip_lower or indicator in field_name_lower 
                  for indicator in data["indicators"]):
                result["is_reused"] = True
                result["reuse_category"] = category
                result["mapping_type"] = data["mapping"]
                break
        
        return result

    def analyze_repeating_field(self, tooltip: str, field_name: str) -> Dict:
        """Analyze if a field is part of a repeating sequence."""
        result = {
            "is_repeating": False,
            "repeating_category": None,
            "sequence_number": None,
            "mapping_type": None
        }
        
        # Check each repeating category's pattern
        for category, data in self.repeating_patterns["categories"].items():
            pattern = data["pattern"]
            match = re.search(pattern, tooltip)
            
            if match:
                result["is_repeating"] = True
                result["repeating_category"] = category
                result["mapping_type"] = data["mapping"]
                
                # Extract sequence number
                sequence = match.group(1)
                if sequence.isdigit():
                    result["sequence_number"] = int(sequence)
                else:
                    # Convert word to number
                    number_map = {"One": 1, "Two": 2, "Three": 3}
                    result["sequence_number"] = number_map.get(sequence, None)
                
                break
            
            # Also check indicators in field name
            if any(indicator in field_name.lower() for indicator in data["indicators"]):
                result["is_repeating"] = True
                result["repeating_category"] = category
                result["mapping_type"] = data["mapping"]
        
        return result

def extract_form_id(text: str) -> Optional[str]:
    """Extract form ID from the field text (e.g., i485, i130)."""
    if not text:
        return None
    
    # Form ID is at the start of the text field
    match = re.match(r'^([a-z]\d+)\s*\t', text.lower())
    if match:
        return match.group(1)
    
    # Try alternate formats
    match = re.search(r'form\s+([a-z][-\s]*\d+)', text.lower())
    if match:
        # Clean up the form ID
        form_id = match.group(1).replace('-', '').replace(' ', '')
        return form_id
    
    return None

def extract_short_label(tooltip: str) -> Optional[str]:
    """Extract short label from tooltip text."""
    if not tooltip:
        return None
        
    # Look for "Select X" or "Enter X" in the last two lines
    lines = [line.strip() for line in tooltip.split('\n') if line.strip()]
    if not lines:
        return None
    
    last_lines = lines[-2:] if len(lines) >= 2 else lines
    
    for line in reversed(last_lines):
        # Look for "Select X" or "Enter X" patterns
        select_match = re.search(r'Select\s+([^.]+)\.?$', line)
        enter_match = re.search(r'Enter\s+([^.]+)\.?$', line)
        
        if select_match:
            return f"Select {select_match.group(1)}"
        elif enter_match:
            return f"Enter {enter_match.group(1)}"
    
    return None

def analyze_fields(fields_file: Path) -> None:
    """Analyze field patterns from the JSON file."""
    with open(fields_file, 'r') as f:
        fields = json.load(f)
    
    # Initialize counters
    form_ids = defaultdict(int)
    field_types = defaultdict(int)
    short_labels = []
    context_patterns = defaultdict(int)
    
    for field in fields:
        # Extract and count form IDs
        form_id = field.get('form_id', 'unknown')
        if form_id:
            form_ids[form_id] += 1
        
        # Count field types
        field_type = field.get('type', 'unknown')
        field_types[field_type] += 1
        
        # Extract short labels for buttons and checkboxes
        if field_type in ('button', 'checkbox'):
            short_label = extract_short_label(field.get('tooltip', ''))
            if short_label:
                short_labels.append({
                    'name': field.get('name', ''),
                    'label': short_label,
                    'type': field_type,
                    'form_id': form_id
                })
        
        # Look for context patterns in tooltips
        tooltip = field.get('tooltip', '')
        if tooltip:
            # Look for common patterns
            if re.search(r'(eye|hair)\s+color', tooltip.lower()):
                context_patterns['physical_characteristics'] += 1
            elif re.search(r'(male|female|gender|sex)', tooltip.lower()):
                context_patterns['gender'] += 1
            elif re.search(r'(sibling|parent|child|stepchild)', tooltip.lower()):
                context_patterns['family_relationship'] += 1
    
    # Print results
    print("\nForm ID Distribution:")
    for form_id, count in sorted(form_ids.items()):
        print(f"{form_id}: {count} fields")
    
    print("\nField Types:")
    for field_type, count in sorted(field_types.items()):
        print(f"{field_type}: {count} fields")
    
    print("\nButton/Checkbox Labels by Form:")
    by_form = defaultdict(list)
    for label_info in short_labels:
        form_id = label_info.get('form_id', 'unknown')
        by_form[form_id].append(label_info)
    
    for form_id, labels in sorted(by_form.items()):
        print(f"\nForm {form_id}:")
        for label_info in labels[:5]:  # Show first 5 per form
            print(f"  {label_info['type']}: {label_info['name']} -> {label_info['label']}")
        if len(labels) > 5:
            print(f"  ... and {len(labels) - 5} more")
    
    print("\nContext Patterns:")
    for pattern, count in sorted(context_patterns.items()):
        print(f"{pattern}: {count} fields")

def save_results(results_df: pd.DataFrame, base_dir: Path):
    """Save analysis results in multiple formats with consistent timestamped directory structure."""
    # Generate timestamp for directory and files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory with timestamp
    output_dir = base_dir / f"analysis_results_{timestamp}"
    output_dir.mkdir(exist_ok=True)
    
    # Save analysis results
    csv_file = output_dir / f"field_analysis_results_{timestamp}.csv"
    json_file = output_dir / f"field_analysis_results_{timestamp}.json"
    table_file = output_dir / f"field_analysis_table_{timestamp}.txt"
    domain_file = output_dir / f"domain_analysis_table_{timestamp}.txt"
    metadata_file = output_dir / f"analysis_metadata_{timestamp}.json"
    
    # Save CSV
    results_df.to_csv(csv_file, index=False)
    
    # Convert DataFrame to JSON-safe dictionary
    def clean_value(val):
        if isinstance(val, (list, np.ndarray)):
            return [clean_value(x) for x in val]
        if pd.isna(val) or val is pd.NA:
            return None
        if isinstance(val, (np.int64, np.int32)):
            return int(val)
        if isinstance(val, (np.float64, np.float32)):
            return float(val)
        if isinstance(val, pd.Timestamp):
            return val.isoformat()
        return str(val) if not isinstance(val, (str, int, float, bool, type(None))) else val

    # Convert DataFrame to records with cleaned values
    results_json = []
    for _, row in results_df.iterrows():
        record = {}
        for column in results_df.columns:
            record[column] = clean_value(row[column])
        results_json.append(record)

    # Save JSON with indentation for readability
    with open(json_file, 'w') as f:
        json.dump(results_json, f, indent=2, default=str)
    
    # Save analysis tables
    with open(table_file, 'w') as f:
        # Field Analysis Summary
        f.write("\n=== Field Analysis Summary ===\n\n")
        f.write(f"Total Fields: {len(results_df)}\n")
        f.write(f"Fields Needing Review: {results_df['needs_review'].sum()} ({results_df['needs_review'].mean()*100:.1f}%)\n\n")
        
        # Form Distribution Summary
        f.write("=== Form Distribution Summary ===\n")
        form_summary = results_df['form_id'].value_counts()
        f.write(form_summary.to_string())
        f.write("\n\n")
        
        # Reused Fields Summary
        f.write("=== Reused Fields Summary ===\n")
        reused_summary = results_df[results_df['is_reused']].groupby(['form_id', 'reuse_category']).size()
        f.write(reused_summary.to_string())
        f.write("\n\n")
        
        # Repeating Fields Summary
        f.write("=== Repeating Fields Summary ===\n")
        repeating_summary = results_df[results_df['is_repeating']].groupby(['form_id', 'repeating_category', 'sequence_number']).size()
        f.write(repeating_summary.to_string())
        f.write("\n\n")
        
        # Persona Distribution
        f.write("=== Persona Distribution ===\n")
        persona_counts = defaultdict(int)
        for personas in results_df['personas'].str.split(';'):
            if isinstance(personas, list):
                for persona in personas:
                    if persona:
                        persona_name = persona.split('(')[0].strip()
                        persona_counts[persona_name] += 1
        
        # Create persona table data
        persona_data = []
        for persona, count in sorted(persona_counts.items()):
            persona_data.append({
                'Persona': persona,
                'Count': count,
                'Percentage': f"{count/len(results_df)*100:.1f}%"
            })
        
        if persona_data:
            persona_table = pd.DataFrame(persona_data)
            f.write("\n" + tabulate(persona_table, headers='keys', tablefmt='grid', showindex=False) + "\n")
    
    # Save domain analysis
    with open(domain_file, 'w') as f:
        f.write("=== Domain Analysis Summary ===\n\n")
        f.write("=== By Form ===\n")
        for form_id in results_df['form_id'].unique():
            form_data = results_df[results_df['form_id'] == form_id]
            f.write(f"\nForm {form_id}:\n")
            domain_counts = defaultdict(int)
            for domains in form_data['domains'].str.split(';'):
                if isinstance(domains, list):
                    for domain in domains:
                        if domain:
                            domain_name = domain.split('(')[0].strip()
                            domain_counts[domain_name] += 1
            
            for domain, count in sorted(domain_counts.items()):
                f.write(f"{domain}: {count} fields ({count/len(form_data)*100:.1f}%)\n")
    
    # Save metadata about the analysis
    metadata = {
        "timestamp": timestamp,
        "total_fields": len(results_df),
        "forms_analyzed": list(results_df['form_id'].unique()),
        "field_types": list(results_df['field_type'].unique()),
        "analysis_version": "2.0"
    }
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return {
        'directory': output_dir,
        'csv': csv_file,
        'json': json_file,
        'table': table_file,
        'domain': domain_file,
        'metadata': metadata_file
    }

def print_summary(results_df: pd.DataFrame, output_files: Dict[str, Path]):
    """Print a summary of the analysis results."""
    # Read and print the table file
    with open(output_files['table'], 'r') as f:
        print(f.read())
    
    # Print example reused fields
    print("\n=== Reused Fields Examples ===")
    reused_fields = results_df[results_df['is_reused']].head()
    reused_examples = pd.DataFrame({
        'Field_Name': reused_fields['field_name'],
        'Reuse_Category': reused_fields['reuse_category'],
        'Mapping_Type': reused_fields['mapping_type'],
        'Field_Type': reused_fields['field_type']
    })
    print(tabulate(reused_examples, headers='keys', tablefmt='grid', showindex=False))
    
    # Print example repeating fields
    print("\n=== Repeating Fields Examples ===")
    repeating_fields = results_df[results_df['is_repeating']].head()
    repeating_examples = pd.DataFrame({
        'Field_Name': repeating_fields['field_name'],
        'Repeating_Category': repeating_fields['repeating_category'],
        'Sequence_Number': repeating_fields['sequence_number'],
        'Field_Type': repeating_fields['field_type']
    })
    print(tabulate(repeating_examples, headers='keys', tablefmt='grid', showindex=False))
    
    # Print output file locations
    print("\n=== Output Files ===")
    print(f"Output Directory: {output_files['directory']}")
    print(f"Detailed CSV: {output_files['csv']}")
    print(f"JSON Results: {output_files['json']}")
    print(f"Analysis Tables: {output_files['table']}")
    print(f"Domain Analysis: {output_files['domain']}")
    print(f"Analysis Metadata: {output_files['metadata']}")

def extract_tooltip_context(tooltip: str) -> Optional[Dict]:
    """Extract meaningful context from tooltips, especially for checkboxes."""
    if not tooltip:
        return None
        
    # Split tooltip into lines and focus on the last two
    lines = [line.strip() for line in tooltip.split('\n') if line.strip()]
    if not lines:
        return None
    
    context = {}
    
    # Look for specific patterns in the last two lines
    last_lines = lines[-2:] if len(lines) >= 2 else lines
    
    # Common patterns to extract meaning
    patterns = {
        'gender': r'(?:gender|sex)\s*(?:is)?\s*(male|female)',
        'eye_color': r'eye\s*color\s*(?:is)?\s*(\w+)',
        'hair_color': r'hair\s*color\s*(?:is)?\s*(\w+)',
        'relationship': r'(?:relationship|beneficiary)\s*(?:type|is)?\s*(sibling|parent|child|stepchild|spouse|adopted)',
        'marital_status': r'marital\s*status\s*(?:is)?\s*(single|married|divorced|widowed|separated)',
        'document_type': r'document\s*(?:type|is)?\s*(passport|visa|i\-\d+|birth certificate|marriage certificate)',
        'yes_no_context': r'(?:select|check|mark)\s+(?:if|when|that)\s+(.+?)(?:\.|$)',
        'binary_choice': r'(?:select|choose)\s+(?:between)?\s*([\w\s]+)\s+(?:or|/)\s*([\w\s]+)'
    }
    
    combined_text = ' '.join(last_lines).lower()
    
    for key, pattern in patterns.items():
        matches = re.search(pattern, combined_text, re.I)
        if matches:
            if key == 'binary_choice':
                context[key] = {'options': [matches.group(1).strip(), matches.group(2).strip()]}
            elif key == 'yes_no_context':
                context[key] = matches.group(1).strip()
            else:
                context[key] = matches.group(1).strip()
    
    return context if context else None

def main():
    """Main function to analyze fields."""
    base_dir = Path(__file__).parent
    fields_file = base_dir / "extracted_fields.json"
    rules_file = base_dir / "field_rules.json"
    mapping_file = base_dir / "field_mappings.json"
    
    if not fields_file.exists():
        print(f"Error: Fields file {fields_file} not found")
        return
        
    if not rules_file.exists():
        print(f"Error: Rules file {rules_file} not found")
        return
        
    if not mapping_file.exists():
        print(f"Error: Mapping file {mapping_file} not found")
        return
    
    # First do basic analysis
    analyze_fields(fields_file)
    
    # Then do comprehensive analysis with FieldAnalyzer
    analyzer = FieldAnalyzer(str(rules_file), str(mapping_file))
    
    # Load fields
    with open(fields_file, 'r') as f:
        fields = json.load(f)
    
    # Analyze each field
    results = []
    for field in fields:
        # Get form ID (e.g., 'i485')
        form_id = field.get('form_id', '')
        
        field_analysis = analyzer.analyze_field(
            field_name=field.get('name', ''),
            tooltip=field.get('tooltip', ''),
            field_type=field.get('type', ''),
            form_id=form_id  # Pass the form ID
        )
        results.append(field_analysis)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Save results and print summary
    output_files = save_results(results_df, base_dir)
    print_summary(results_df, output_files)

if __name__ == '__main__':
    main() 