import csv
from collections import defaultdict

def create_simple_map(input_filepath, output_filepath):
    """
    Parses the mapped_fields_output.csv to create a de-duplicated and
    sectioned simple_map.csv.
    """
    # Key: (i485_label, i485_field_original)
    # Value: {'i485_field_normalized': str, 'jira_matches': set((jira_name, jira_id)), 'has_any_valid_match': bool}
    processed_data = {}

    try:
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                i485_label = row.get('I-485 Label', '').strip()
                i485_field_original = row.get('I-485 Field (Original)', '').strip()
                
                if not i485_label and not i485_field_original: # Need at least one to form a key
                    continue

                current_key = (i485_label, i485_field_original)

                if current_key not in processed_data:
                    processed_data[current_key] = {
                        'i485_field_normalized': row.get('I-485 Field (Normalized)', ''),
                        'jira_matches': set(),  # To store (Jira Name, Jira ID) tuples
                        'has_any_valid_match': False # Tracks if this specific pair got any valid Jira match
                    }
                
                # If Match Status is 'Matched', it means I-485 Field (Normalized) == Jira Field Name (Normalized)
                # for this specific row in mapped_fields_output.csv.
                # This is the condition we want for associating this Jira field with this I-485 field.
                if row.get('Match Status', '') == 'Matched':
                    jira_name = row.get('Jira Field Name (Original)', '').strip()
                    jira_id = row.get('Jira Field ID', '').strip()
                    if jira_name and jira_id: # Only add if both Jira name and ID are present
                        processed_data[current_key]['jira_matches'].add((jira_name, jira_id))
                        processed_data[current_key]['has_any_valid_match'] = True
                # If 'Match Status' is 'No Match', we don't add the Jira field from this row,
                # but the (I-485 Label, I-485 Field (Original)) pair might still exist from other rows
                # or will be added to the 'unmatched_list' if it never gets a valid match.

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_filepath}")
        return
    except Exception as e:
        print(f"Error reading input CSV {input_filepath}: {e}")
        return

    matched_list = []
    unmatched_list = []

    for (label_key, field_original_key), data in processed_data.items():
        item_for_list = {
            'i485_label': label_key,
            'i485_field_original': field_original_key,
            'i485_field_normalized': data['i485_field_normalized'],
            'jira_matches_set': data['jira_matches'] # Keep the set for now
        }
        # An (I-485 Label, I-485 Field Original) pair is considered matched if it
        # accumulated any valid Jira matches.
        if data['has_any_valid_match'] and data['jira_matches']:
            matched_list.append(item_for_list)
        else:
            # This covers 'No Match' status, or 'Matched' status but no actual jira_matches were collected
            unmatched_list.append(item_for_list)
            
    # Sort lists for consistent output, e.g., by I-485 label
    # Custom sort key using padded numeric parts for correct sorting
    def sort_key(item):
        label = item['i485_label']
        parts = label.split('.')
        sortable_parts = []
        for part in parts:
            if part.isdigit():
                sortable_parts.append(f"{int(part):05d}") # Pad numeric parts
            else:
                sortable_parts.append(part) # Keep non-numeric parts as strings
        return tuple(sortable_parts)

    matched_list.sort(key=sort_key)
    unmatched_list.sort(key=sort_key)


    try:
        with open(output_filepath, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)

            # --- Matched Section ---
            writer.writerow(['Section Header', 'Description'])
            writer.writerow(['Fields Matched', len(matched_list)])
            writer.writerow(['I-485 Label', 'I-485 Field (Original)', 'I-485 Field (Normalized)', 'Jira Matches (Name - ID)'])
            
            for item in matched_list:
                # Sort Jira matches for consistent string representation
                sorted_jira_matches = sorted(list(item['jira_matches_set']))
                jira_matches_str = "; ".join([f"{name} - {id}" for name, id in sorted_jira_matches])
                writer.writerow([
                    item['i485_label'],
                    item['i485_field_original'],
                    item['i485_field_normalized'],
                    jira_matches_str
                ])

            writer.writerow([]) # Empty row as a separator

            # --- Not Matched Section ---
            writer.writerow(['Section Header', 'Description'])
            writer.writerow(['Fields not Matched', len(unmatched_list)])
            writer.writerow(['I-485 Label', 'I-485 Field (Original)', 'I-485 Field (Normalized)', 'Jira Matches (Name - ID)']) # Include header for consistency

            for item in unmatched_list:
                writer.writerow([
                    item['i485_label'],
                    item['i485_field_original'],
                    item['i485_field_normalized'],
                    '' # No Jira matches for this section
                ])
        
        print("\n--- Summary of items written to simple_map.csv ---")
        print(f"Number of unique (I-485 Label, I-485 Field Original) pairs with Jira matches: {len(matched_list)}")
        print(f"Number of unique (I-485 Label, I-485 Field Original) pairs without Jira matches: {len(unmatched_list)}")
        print(f"Successfully created de-duplicated map: {output_filepath}")

    except Exception as e:
        print(f"Error writing output CSV {output_filepath}: {e}")

if __name__ == '__main__':
    input_csv = '/Users/amyamylloyd/ImLaw/generalscripts/mapped_fields_output.csv'
    output_csv = '/Users/amyamylloyd/ImLaw/generalscripts/simple_map.csv'
    create_simple_map(input_csv, output_csv)

