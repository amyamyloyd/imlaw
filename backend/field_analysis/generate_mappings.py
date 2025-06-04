import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class MappingGenerator:
    def __init__(self, collection_schema_file: str, mapping_schema_file: str):
        """Initialize with collection and mapping schemas."""
        with open(collection_schema_file, 'r') as f:
            self.collections = json.load(f)
        with open(mapping_schema_file, 'r') as f:
            self.mapping_schema = json.load(f)
        
        # Compile regex patterns
        self.sequence_patterns = {
            name: re.compile(pattern["regex"]) 
            for name, pattern in self.mapping_schema["mapping_rules"]["sequence_detection"]["patterns"].items()
        }
        
        # Common patterns for tooltip context
        self.tooltip_patterns = {
            'gender': re.compile(r'(?:gender|sex)\s*(?:is)?\s*(male|female)', re.I),
            'eye_color': re.compile(r'eye\s*color\s*(?:is)?\s*(\w+)', re.I),
            'hair_color': re.compile(r'hair\s*color\s*(?:is)?\s*(\w+)', re.I),
            'relationship': re.compile(r'(?:relationship|beneficiary)\s*(?:type|is)?\s*(sibling|parent|child|stepchild|spouse|adopted)', re.I),
            'marital_status': re.compile(r'marital\s*status\s*(?:is)?\s*(single|married|divorced|widowed|separated)', re.I),
            'document_type': re.compile(r'document\s*(?:type|is)?\s*(passport|visa|i\-\d+|birth certificate|marriage certificate)', re.I),
            'yes_no_context': re.compile(r'(?:select|check|mark)\s+(?:if|when|that)\s+(.+?)(?:\.|$)', re.I),
            'binary_choice': re.compile(r'(?:select|choose)\s+(?:between)?\s*([\w\s]+)\s+(?:or|/)\s*([\w\s]+)', re.I)
        }

    def extract_tooltip_context(self, tooltip: str) -> Optional[Dict]:
        """Extract context from tooltip text."""
        if not tooltip:
            return None
            
        # Split tooltip into lines and focus on the last two
        lines = [line.strip() for line in tooltip.split('\n') if line.strip()]
        if not lines:
            return None
        
        context = {}
        combined_text = ' '.join(lines[-2:] if len(lines) >= 2 else lines)
        
        for context_type, pattern in self.tooltip_patterns.items():
            match = pattern.search(combined_text)
            if match:
                if context_type == 'binary_choice':
                    context[context_type] = {'options': [match.group(1).strip(), match.group(2).strip()]}
                else:
                    context[context_type] = match.group(1).strip()
        
        return context if context else None

    def detect_sequence(self, field_name: str, tooltip: str) -> Optional[Tuple[str, int]]:
        """Detect if field is part of a sequence (e.g., Address 1, Employer 2)."""
        combined_text = f"{field_name} {tooltip}"
        
        for seq_type, pattern in self.sequence_patterns.items():
            match = pattern.search(combined_text)
            if match:
                index = int(match.group(1))
                return seq_type, index
        
        return None

    def get_collection_field(self, field_type: str, sequence_info: Optional[Tuple[str, int]] = None, tooltip_context: Optional[Dict] = None) -> str:
        """Map a field type to its collection field path."""
        # Check direct mappings first
        if field_type in self.mapping_schema["mapping_rules"]["field_type_mappings"]:
            mapping = self.mapping_schema["mapping_rules"]["field_type_mappings"][field_type]
            
            # Handle different mapping types
            if isinstance(mapping, dict):
                # Handle address-style mappings with current/historical
                if "current" in mapping and "historical" in mapping:
                    if sequence_info:
                        return mapping["historical"].replace("[i]", f"[{sequence_info[1]-1}]")
                    return mapping["current"]
                
                # Handle date fields that depend on context
                if sequence_info and sequence_info[0] in mapping:
                    return mapping[sequence_info[0]].replace("[i]", f"[{sequence_info[1]-1}]")
                
                # Use first available mapping if context not clear
                return next(iter(mapping.values()))
            
            # Handle relationship assignments
            elif isinstance(mapping, str) and "=" in mapping:
                field_path, value = mapping.split("=")
                if sequence_info:
                    field_path = field_path.replace("[i]", f"[{sequence_info[1]-1}]")
                return f"{field_path}={value}"
            
            # Handle simple string mappings
            else:
                return mapping
        
        # Check tooltip context mappings
        if tooltip_context:
            context_mappings = self.mapping_schema["mapping_rules"].get("tooltip_context_mappings", {})
            for context_type, value in tooltip_context.items():
                if context_type in context_mappings:
                    mapping = context_mappings[context_type]
                    if isinstance(value, dict) and "options" in value:
                        return f"{mapping}={json.dumps(value['options'])}"
                    return f"{mapping}={value}"
        
        return None

    def generate_field_mapping(self, field_data: Dict) -> Dict:
        """Generate mapping for a single field."""
        field_name = field_data["Field_Name"]
        base_type = field_data["Base_Field_Type"]
        tooltip = field_data["Tooltip"]
        
        # Initialize mapping
        mapping = {
            "field_name": field_name,
            "collection_field": None,
            "persona": field_data.get("Personas", "unknown").split(";")[0].split("(")[0].strip(),
            "is_sequence": False,
            "sequence_type": None,
            "sequence_index": None,
            "context": None
        }
        
        # Check if it's an office field
        if "office" in field_data.get("Domains", "").lower():
            mapping["collection_field"] = f"office.{base_type.lower()}"
            return mapping
        
        # Extract tooltip context for checkboxes and yes/no fields
        tooltip_context = None
        if base_type in ["CB", "Checkbox", "Yes", "No", "YesNo"]:
            tooltip_context = self.extract_tooltip_context(tooltip)
            if tooltip_context:
                mapping["context"] = tooltip_context
        
        # Detect sequences
        sequence_info = self.detect_sequence(field_name, tooltip)
        if sequence_info:
            mapping["is_sequence"] = True
            mapping["sequence_type"] = sequence_info[0]
            mapping["sequence_index"] = sequence_info[1]
        
        # Get collection field path
        collection_field = self.get_collection_field(base_type, sequence_info, tooltip_context)
        if collection_field:
            mapping["collection_field"] = collection_field
            
            # For relationship assignments, also set the sequence info
            if "=" in str(collection_field):
                mapping["is_sequence"] = True
                mapping["sequence_type"] = "family"
                # Use a counter or derive index from existing family members
                mapping["sequence_index"] = 1  # This should be managed by the application
        
        return mapping

    def generate_all_mappings(self, analysis_results: List[Dict]) -> Dict:
        """Generate mappings for all analyzed fields."""
        mappings = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "field_mappings": {}
        }
        
        for field_data in analysis_results:
            mapping = self.generate_field_mapping(field_data)
            mappings["field_mappings"][field_data["Field_Name"]] = mapping
        
        return mappings

def main():
    """Main execution function."""
    # Set up paths
    base_dir = Path(__file__).parent
    collection_schema = base_dir / "collection_schema.json"
    mapping_schema = base_dir / "field_mappings.json"
    
    # Find most recent analysis results
    analysis_dirs = sorted(
        [d for d in base_dir.glob("analysis_results_*") if d.is_dir()],
        key=lambda x: x.name,
        reverse=True
    )
    if not analysis_dirs:
        print("No analysis results found!")
        return
    
    # Get the timestamp from the directory name
    timestamp = analysis_dirs[0].name.split("analysis_results_")[-1]
    latest_results = analysis_dirs[0] / f"field_analysis_results_{timestamp}.json"
    
    print(f"Using analysis results from: {latest_results}")
    
    # Load analysis results
    with open(latest_results, 'r') as f:
        analysis_results = json.load(f)
    
    # Generate mappings
    generator = MappingGenerator(str(collection_schema), str(mapping_schema))
    mappings = generator.generate_all_mappings(analysis_results)
    
    # Save mappings
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = base_dir / f"generated_mappings_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(mappings, f, indent=2)
    
    print(f"\nGenerated mappings saved to: {output_file}")
    
    # Print summary
    total_fields = len(mappings["field_mappings"])
    mapped_fields = sum(1 for m in mappings["field_mappings"].values() if m["collection_field"])
    sequence_fields = sum(1 for m in mappings["field_mappings"].values() if m["is_sequence"])
    context_fields = sum(1 for m in mappings["field_mappings"].values() if m.get("context"))
    
    print("\nMapping Summary:")
    print(f"Total fields processed: {total_fields}")
    print(f"Successfully mapped: {mapped_fields} ({mapped_fields/total_fields*100:.1f}%)")
    print(f"Sequence fields: {sequence_fields} ({sequence_fields/total_fields*100:.1f}%)")
    print(f"Context-aware fields: {context_fields} ({context_fields/total_fields*100:.1f}%)")
    
    # Group by collection field to show reuse
    collection_usage = {}
    for mapping in mappings["field_mappings"].values():
        if mapping["collection_field"]:
            collection_usage[mapping["collection_field"]] = collection_usage.get(mapping["collection_field"], 0) + 1
    
    print("\nTop reused collection fields:")
    for field, count in sorted(collection_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{field}: {count} uses")

if __name__ == "__main__":
    main() 