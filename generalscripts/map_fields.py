import csv
import re
from collections import defaultdict

def normalize_field_name(name):
    """
    Normalizes a field name for comparison.
    - Converts to lowercase.
    - Removes content within parentheses.
    - Removes most punctuation (keeps hyphens).
    - Normalizes whitespace.
    """
    if not isinstance(name, str):
        return ""
    
    # Lowercase
    processed_name = name.lower()
    
    # Remove content within parentheses (e.g., (mm/dd/yyyy), (if any))
    # Replace with a space to avoid merging words accidentally
    processed_name = re.sub(r'\s*\([^)]*\)\s*', ' ', processed_name)
    
    # Specific prefixes that are common in the Jira data and might not be in I-485
    # This helps align names if one source is more verbose.
    prefixes_to_strip = [
        "i-485:", "social security card:", "additional information about you:",
        "current mailing address safe or alternate mailing address if applicable :", # Note the space and colon
        "current u.s. physical address:", "employment and educational history:",
        "location of u.s. embassy or u.s. consulate-",
        "most recent address outside the united states:", "prior address:"
    ]
    for prefix in prefixes_to_strip:
        if processed_name.startswith(prefix.lower()):
            processed_name = processed_name[len(prefix):].strip()

    # Handle specific common variations like "apt., ste., flr."
    processed_name = processed_name.replace("apt., ste., flr.", "apt ste flr")
    processed_name = processed_name.replace("apt., sye., flr.", "apt ste flr") # Typo in Jira data

    # Remove punctuation except hyphens (useful for terms like "A-Number")
    # Replace with space to avoid merging words
    processed_name = re.sub(r'[^\w\s-]', ' ', processed_name) # \w includes letters, numbers, and underscore
    processed_name = processed_name.replace('_', ' ') # Replace underscore with space
    
    # Normalize whitespace (strip leading/trailing, reduce multiple spaces to one)
    processed_name = ' '.join(processed_name.split())
    
    return processed_name.strip()

def load_i485_fields(filepath):
    """Loads and processes fields from the I-485 CSV."""
    i485_fields = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Skip the first line which is a title
            next(f) 
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2): # start=2 because we skipped one line and DictReader uses the next as header
                i485_field_val = row.get('Field', '').strip()
                i485_label_val = row.get('Label', '').strip()
                
                if i485_field_val: # Only process if 'Field' column has content
                    normalized = normalize_field_name(i485_field_val)
                    i485_fields.append({
                        "label": i485_label_val,
                        "field_original": i485_field_val,
                        "field_normalized": normalized,
                        "row_number": row_num 
                    })
                # else:
                #     print(f"Skipping I-485 row {row_num} due to empty 'Field': Label='{i485_label_val}'")
    except FileNotFoundError:
        print(f"Error: I-485 file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error reading I-485 CSV {filepath}: {e}")
        return None
    return i485_fields

def load_jira_fields(filepath):
    """Loads and processes fields from the Jira CSV, creating a lookup map."""
    jira_lookup = defaultdict(list)
    raw_jira_fields = [] # To store all Jira fields for reference if needed
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=1):
                jira_name = row.get('Field Name', '').strip()
                jira_id = row.get('Field ID', '').strip()
                
                if jira_name and jira_id:
                    normalized = normalize_field_name(jira_name)
                    field_data = {
                        "name_original": jira_name,
                        "id": jira_id,
                        "name_normalized": normalized,
                        "row_number": row_num
                    }
                    jira_lookup[normalized].append(field_data)
                    raw_jira_fields.append(field_data)
                # else:
                #     print(f"Skipping Jira row {row_num} due to empty 'Field Name' or 'Field ID'.")
    except FileNotFoundError:
        print(f"Error: Jira file not found at {filepath}")
        return None, None
    except Exception as e:
        print(f"Error reading Jira CSV {filepath}: {e}")
        return None, None
    return jira_lookup, raw_jira_fields

def main():
    i485_filepath = '/Users/amyamylloyd/ImLaw/generalscripts/i485 Fields - Sheet1.csv'
    jira_filepath = '/Users/amyamylloyd/ImLaw/generalscripts/jira_fields_output.csv'

    print(f"Loading I-485 fields from: {i485_filepath}")
    i485_data = load_i485_fields(i485_filepath)
    if i485_data is None:
        return

    print(f"\nLoading Jira fields from: {jira_filepath}")
    jira_lookup_map, _ = load_jira_fields(jira_filepath) # We don't need raw_jira_fields here
    if jira_lookup_map is None:
        return

    print("\n--- Field Mapping Results ---")
    
    total_i485_fields_processed = 0
    matched_i485_fields = 0
    
    all_mappings = []

    for i485_item in i485_data:
        total_i485_fields_processed += 1
        
        current_mapping = {
            "i485_label": i485_item['label'],
            "i485_field_original": i485_item['field_original'],
            "i485_field_normalized": i485_item['field_normalized'],
            "jira_matches": []
        }

        print(f"\nI-485 Label: '{i485_item['label']}' | Field: \"{i485_item['field_original']}\"")
        print(f"  Normalized I-485: \"{i485_item['field_normalized']}\"")

        found_matches = jira_lookup_map.get(i485_item['field_normalized'], [])
        
        if found_matches:
            matched_i485_fields += 1
            print("  Jira Matches Found:")
            for match in found_matches:
                print(f"    - Jira Field: \"{match['name_original']}\" (ID: {match['id']})")
                print(f"      Normalized Jira: \"{match['name_normalized']}\"")
                current_mapping["jira_matches"].append({
                    "jira_field_name": match['name_original'],
                    "jira_field_id": match['id'],
                    "jira_field_normalized": match['name_normalized']
                })
        else:
            print("  No Jira matches found based on current normalization.")
        
        all_mappings.append(current_mapping)

    print("\n--- Summary ---")
    print(f"Total I-485 fields (with non-empty 'Field' column) processed: {total_i485_fields_processed}")
    print(f"I-485 fields with at least one Jira match: {matched_i485_fields}")
    print(f"I-485 fields with no Jira matches: {total_i485_fields_processed - matched_i485_fields}")

    # You can now use `all_mappings` list of dictionaries for further processing
    # For example, to write to a new CSV or JSON file.
    # Example: Outputting to a simple CSV for matched fields
    output_csv_path = '/Users/amyamylloyd/ImLaw/generalscripts/mapped_fields_output.csv'
    print(f"\nWriting detailed mapping to: {output_csv_path}")
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = [
                'I-485 Label', 'I-485 Field (Original)', 'I-485 Field (Normalized)',
                'Jira Field Name (Original)', 'Jira Field ID', 'Jira Field Name (Normalized)', 'Match Status'
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in all_mappings:
                if item['jira_matches']:
                    for jira_match in item['jira_matches']:
                        writer.writerow({
                            'I-485 Label': item['i485_label'],
                            'I-485 Field (Original)': item['i485_field_original'],
                            'I-485 Field (Normalized)': item['i485_field_normalized'],
                            'Jira Field Name (Original)': jira_match['jira_field_name'],
                            'Jira Field ID': jira_match['jira_field_id'],
                            'Jira Field Name (Normalized)': jira_match['jira_field_normalized'],
                            'Match Status': 'Matched'
                        })
                else:
                    writer.writerow({
                        'I-485 Label': item['i485_label'],
                        'I-485 Field (Original)': item['i485_field_original'],
                        'I-485 Field (Normalized)': item['i485_field_normalized'],
                        'Jira Field Name (Original)': '',
                        'Jira Field ID': '',
                        'Jira Field Name (Normalized)': '',
                        'Match Status': 'No Match'
                    })
        print(f"Successfully wrote mapping results to {output_csv_path}")
    except Exception as e:
        print(f"Error writing output CSV: {e}")

if __name__ == '__main__':
    main()
