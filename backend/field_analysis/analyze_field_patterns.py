import json
import pandas as pd
import re
from typing import Dict, List, Tuple
from pathlib import Path
from tabulate import tabulate
from datetime import datetime
from collections import defaultdict

class FieldAnalyzer:
    def __init__(self, rules_file: str, mapping_file: str):
        """Initialize with rules and mapping configurations."""
        with open(rules_file, 'r') as f:
            self.rules = json.load(f)
        with open(mapping_file, 'r') as f:
            self.mappings = json.load(f)
            
        # Define personas
        self.personas = {
            "applicant": {
                "indicators": [
                    "you", "your", "applicant", "beneficiary", "self",
                    "i am", "i have", "my ", "principal", "client"
                ],
                "confidence": 2.0
            },
            "family": {
                "indicators": [
                    "spouse", "husband", "wife", "child", "parent",
                    "mother", "father", "sibling", "brother", "sister",
                    "dependent", "relative", "family member"
                ],
                "confidence": 1.8
            },
            "preparer": {
                "indicators": [
                    "attorney", "lawyer", "paralegal", "interpreter",
                    "translator", "notary", "accredited representative",
                    "preparer", "law office", "firm", "representative"
                ],
                "confidence": 1.5
            }
        }

        # Define biographical subcategories
        self.biographical_subcategories = {
            "core_identity": {
                "indicators": [
                    "name", "birth", "gender", "sex", "race", "ethnicity",
                    "height", "weight", "eye color", "hair color", "biometric",
                    "ssn", "social security", "date of birth"
                ],
                "confidence": 1.8
            },
            "contact_info": {
                "indicators": [
                    "address", "phone", "email", "telephone", "mobile",
                    "mailing", "street", "city", "state", "zip", "postal",
                    "country", "residence", "contact"
                ],
                "confidence": 1.6
            },
            "marital_status": {
                "indicators": [
                    "married", "single", "divorced", "widowed", "marriage",
                    "separation", "wedding", "spouse", "husband", "wife",
                    "marital status"
                ],
                "confidence": 1.7
            },
            "family_info": {
                "indicators": [
                    "children", "siblings", "parents", "mother", "father",
                    "brother", "sister", "dependent", "family member",
                    "relative", "household", "family unit", "family composition"
                ],
                "confidence": 1.7
            },
            "education": {
                "indicators": [
                    "school", "education", "degree", "diploma", "university",
                    "college", "academic", "study", "student"
                ],
                "confidence": 1.5
            }
        }

        # Domain indicators remain but biographical is now more general
        self.domain_indicators = {
            "biographical": [
                "personal", "individual", "identity", "background",
                "information", "details", "profile"
            ],
            "medical": [
                "surgery", "medical", "examination", "health", "treatment",
                "medication", "hospitalization", "diagnosis", "condition"
            ],
            "criminal": [
                "criminal", "arrest", "detained", "violations", "charges",
                "controlled substances", "inadmissibility grounds"
            ],
            "immigration": [
                "visa", "status", "entry", "admission", "citizenship",
                "permanent resident", "alien", "immigration", "naturalization",
                "passport", "border", "port of entry", "alien number", 
                "uscis number", "travel document", "volag number",
                "arrival-departure record", "recipient number",
                "principals underlying petition"
            ],
            "employment": [
                "job", "work", "employer", "salary", "occupation",
                "business", "income", "employment", "company", "position"
            ],
            "office": [
                "barcode", "pdf417", "qr code", "scan"
            ]
        }

        # Special field patterns
        self.composite_patterns = [
            "uscis", "alien number", "ssn", "arrival-departure record number",
            "recipient number", "principals underlying petition number"
        ]
        
        self.ignore_patterns = [
            "page number", "part number", "item number"
        ]

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

    def analyze_field(self, field_name: str, tooltip: str, field_type: str) -> Dict:
        """Analyze a single field and return its properties."""
        # Parse field name components
        parsed = self.parse_field_name(field_name)
        
        # Initialize result
        result = {
            "field_name": field_name,
            "tooltip": tooltip,
            "field_type": field_type,
            "needs_review": False,
            "confidence": 0.0,
            "domains": [],
            "personas": [],
            "biographical_subcategories": []
        }
        result.update(parsed)  # Add parsed field name components
        
        # Special handling for Checkbox fields
        if field_name.startswith('Checkbox'):
            # Extract base field type from tooltip
            if tooltip:
                # Try to find "Select this box" instruction
                select_match = re.search(r'Select this box (.+?)\.', tooltip)
                if select_match:
                    result["base_field_type"] = select_match.group(1).strip()
                else:
                    # Use the last sentence as the base field type
                    sentences = re.split(r'[.!?]+', tooltip)
                    if sentences:
                        result["base_field_type"] = sentences[-1].strip()
        
        # Special handling for AttorneyStateBarNumber
        if field_name.startswith('AttorneyStateBarNumber'):
            result["domains"] = [("office", 2.0)]  # High confidence for office domain
            result["personas"] = [("preparer", 2.0)]  # High confidence for preparer persona
            result["confidence"] = 2.0
        
        # Apply domain rules
        if not result["domains"]:  # Only if not already set by special rules
            result["domains"] = self.analyze_domain(tooltip)
        
        # Apply persona rules
        if not result["personas"]:  # Only if not already set by special rules
            result["personas"] = self.analyze_persona(tooltip, field_name)
        
        # Apply biographical subcategory rules
        if not result["biographical_subcategories"]:
            result["biographical_subcategories"] = self.analyze_biographical_subcategory(tooltip, field_name)
        
        # Calculate overall confidence
        if not result["confidence"]:  # Only if not already set by special rules
            confidences = [conf for _, conf in result["domains"]]
            result["confidence"] = max(confidences) if confidences else 0.0
        
        return result

def analyze_fields(csv_file: str, rules_file: str, mapping_file: str) -> pd.DataFrame:
    """Analyze all fields in the CSV and return results as a DataFrame."""
    # Read input CSV
    df = pd.read_csv(csv_file)
    
    # Initialize analyzer
    analyzer = FieldAnalyzer(rules_file, mapping_file)
    
    # Analyze each field
    results = []
    for _, row in df.iterrows():
        analysis = analyzer.analyze_field(
            row['Field Name'],
            row['Tooltip'],
            row['Type']
        )
        
        # Convert analysis to flat structure for DataFrame
        flat_result = {
            'Field_Name': analysis['field_name'],
            'Tooltip': analysis['tooltip'],
            'Field_Type': analysis['field_type'],
            'Needs_Review': analysis['needs_review'],
            'Confidence': analysis['confidence'],
            'Part': analysis['part'],
            'Part_Num': analysis['part_num'],
            'Line': analysis['line'],
            'Subline': analysis['subline'],
            'Base_Field_Type': analysis.get('base_field_type', analysis['field_type']),
            'Position': analysis['position'],
            'Domains': '; '.join(f"{d}({c})" for d, c in analysis['domains']),
            'Personas': '; '.join(f"{p}({c})" for p, c in analysis['personas']),
            'Biographical_Subcategories': '; '.join(f"{s}({c})" for s, c in analysis['biographical_subcategories'])
        }
        results.append(flat_result)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    return results_df

def save_results(results_df: pd.DataFrame, base_dir: Path):
    """Save analysis results in multiple formats."""
    # Generate timestamp for files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory with timestamp
    output_dir = base_dir / f"analysis_results_{timestamp}"
    output_dir.mkdir(exist_ok=True)
    
    # Save as CSV
    csv_file = output_dir / f"field_analysis_results_{timestamp}.csv"
    results_df.to_csv(csv_file, index=False)
    
    # Save as JSON
    json_file = output_dir / f"field_analysis_results_{timestamp}.json"
    results_json = results_df.to_dict(orient='records')
    with open(json_file, 'w') as f:
        json.dump(results_json, f, indent=2)
    
    # Create domain summary table
    domain_counts = defaultdict(int)
    for domains in results_df['Domains'].str.split(';'):
        if isinstance(domains, list):
            for domain in domains:
                if domain:
                    domain_name = domain.split('(')[0].strip()
                    domain_counts[domain_name] += 1
    
    domain_table = pd.DataFrame([
        {'Domain': domain, 'Count': count, '% of Total Fields': f"{count/len(results_df)*100:.1f}%"}
        for domain, count in domain_counts.items()
    ]).sort_values('Count', ascending=False)
    
    domain_table_file = output_dir / f"domain_analysis_table_{timestamp}.txt"
    with open(domain_table_file, 'w') as f:
        f.write("=== Domain Distribution ===\n")
        f.write(domain_table.to_string(index=False))
    
    # Create biographical subcategory summary table
    bio_counts = defaultdict(int)
    for subcats in results_df['Biographical_Subcategories'].str.split(';'):
        if isinstance(subcats, list):
            for subcat in subcats:
                if subcat:
                    subcat_name = subcat.split('(')[0].strip()
                    bio_counts[subcat_name] += 1
    
    bio_table = pd.DataFrame([
        {'Subcategory': subcat, 'Count': count, '% of Total Fields': f"{count/len(results_df)*100:.1f}%"}
        for subcat, count in bio_counts.items()
    ]).sort_values('Count', ascending=False)
    
    # Create persona summary table
    persona_counts = defaultdict(int)
    for personas in results_df['Personas'].str.split(';'):
        if isinstance(personas, list):
            for persona in personas:
                if persona:
                    persona_name = persona.split('(')[0].strip()
                    persona_counts[persona_name] += 1
    
    persona_table = pd.DataFrame([
        {'Persona': persona, 'Count': count, '% of Total Fields': f"{count/len(results_df)*100:.1f}%"}
        for persona, count in persona_counts.items()
    ]).sort_values('Count', ascending=False)
    
    # Save summary tables to a single file
    summary_file = output_dir / f"field_analysis_table_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("\n=== Field Analysis Summary ===\n\n")
        f.write(f"Total Fields: {len(results_df)}\n")
        f.write(f"Fields Needing Review: {results_df['Needs_Review'].sum()} ({results_df['Needs_Review'].mean()*100:.1f}%)\n\n")
        
        f.write("=== Persona Distribution ===\n")
        f.write(persona_table.to_string(index=False))
        f.write("\n\n=== Biographical Subcategory Distribution ===\n")
        f.write(bio_table.to_string(index=False))
        f.write("\n\n=== Domain Distribution ===\n")
        f.write(domain_table.to_string(index=False))
    
    # Save metadata about the analysis
    metadata = {
        'timestamp': timestamp,
        'total_fields': len(results_df),
        'fields_needing_review': int(results_df['Needs_Review'].sum()),
        'review_percentage': float(results_df['Needs_Review'].mean()*100),
        'output_files': {
            'csv': str(csv_file.name),
            'json': str(json_file.name),
            'summary': str(summary_file.name),
            'domain_analysis': str(domain_table_file.name)
        }
    }
    
    metadata_file = output_dir / f"analysis_metadata_{timestamp}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Return paths to all output files
    return {
        'csv': csv_file,
        'json': json_file,
        'summary': summary_file,
        'domain_analysis': domain_table_file,
        'metadata': metadata_file
    }

def print_summary(results_df: pd.DataFrame, output_files: Dict[str, Path]):
    """Print a summary of the analysis results."""
    # Read the summary file
    with open(output_files['summary'], 'r') as f:
        print(f.read())
    
    # Print example biographical fields
    print("\n=== Biographical Field Examples ===")
    bio_fields = results_df[
        results_df['Domains'].str.contains('biographical', case=False, na=False)
    ].head()
    
    bio_examples = pd.DataFrame({
        'Field_Name': bio_fields['Field_Name'],
        'Persona': bio_fields['Personas'],
        'Biographical_Subcategories': bio_fields['Biographical_Subcategories'],
        'Domains': bio_fields['Domains']
    })
    
    print(tabulate(
        bio_examples,
        headers='keys',
        tablefmt='grid',
        showindex=False
    ))
    
    # Print output file locations
    print("\n=== Output Files ===")
    print(f"Output Directory: {output_files['summary'].parent}")
    print(f"Detailed CSV: {output_files['csv']}")
    print(f"JSON: {output_files['json']}")
    print(f"Summary Table: {output_files['summary']}")
    print(f"Domain Analysis: {output_files['domain_analysis']}")
    print(f"Analysis Metadata: {output_files['metadata']}")

def main():
    """Main execution function."""
    # Set up paths
    base_dir = Path(__file__).parent
    rules_file = base_dir / "field_rules.json"
    mapping_file = base_dir / "field_mapping.json"
    input_file = base_dir / "fieldswrules.csv"
    
    # Run analysis
    results_df = analyze_fields(str(input_file), str(rules_file), str(mapping_file))
    
    # Save results in multiple formats
    output_files = save_results(results_df, base_dir)
    
    # Print summary and preview
    print_summary(results_df, output_files)

if __name__ == "__main__":
    main() 