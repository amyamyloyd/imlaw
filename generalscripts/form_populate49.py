import csv
import json
import re

def normalize_label_text(label_text):
    """Normalizes form item labels like '1. A.' or 'Pt1Line1a' to a consistent format e.g., '1a'."""
    if not isinstance(label_text, str):
        return ""
    processed_label = label_text.lower()
    processed_label = re.sub(r'^pt\d*line', '', processed_label)
    processed_label = re.sub(r'^(item\s*number|item)\s*', '', processed_label, flags=re.IGNORECASE)
    processed_label = re.sub(r'[\s\._\[\]\(\)\:]', '', processed_label)
    return processed_label.strip()

def extract_item_labels_from_tooltip(tooltip_text):
    """Extracts and normalizes potential item labels (e.g., '1. A.') from a tooltip string."""
    if not isinstance(tooltip_text, str):
        return []
    
    normalized_labels = set()
    
    # Pattern for ". <digit>. <Letter>." (e.g., ". 1. A. Enter...")
    # Captures the "1. A" or "1. A." part.
    user_pattern_matches = re.findall(r'\.\s*(\d+\s*\.\s*[A-Za-z](?:\s*\.)?)(?=\s|\b|$)', tooltip_text)
    for match in user_pattern_matches:
        normalized_labels.add(normalize_label_text(match))

    # General pattern for X.Y. starting at a word boundary (e.g., "1. A.", "23.B.")
    general_xy_matches = re.findall(r'\b(\d+\s*\.\s*[A-Za-z](?:\s*\.)?)(?=\s|\b|$)', tooltip_text)
    for match in general_xy_matches:
        normalized_labels.add(normalize_label_text(match))
        
    # Pattern for "Item Number X.Y" or "Item X.Y"
    item_num_matches = re.findall(r'\bItem(?:\s*Number)?\s*(\d+\s*\.?\s*[A-Za-z]?\s*\.?)', tooltip_text, re.IGNORECASE)
    for m in item_num_matches:
        normalized_labels.add(normalize_label_text(m))

    # Pattern for just a number if it's a main item (e.g., "5. Enter Date of Birth")
    # Ensure it's followed by a dot and then typically a space or end of word/string.
    single_num_matches = re.findall(r'\b(\d+)\s*\.(?=\s|\b|$)', tooltip_text)
    for m in single_num_matches:
        # Avoid adding "5" if "5a" is already there from a more specific pattern.
        is_substring_of_existing = any(m == nl[:len(m)] and len(nl) > len(m) for nl in normalized_labels)
        if not is_substring_of_existing:
            normalized_labels.add(normalize_label_text(m))
            
    return list(normalized_labels)

def normalize_text_for_comparison(text):
    """
    Consistent normalization for comparing PDF tooltips, I-485 field names, and Jira field names.
    """
    if not isinstance(text, str):
        return ""
    
    processed_text = text.lower()
    processed_text = re.sub(r'\s*\([^)]*\)\s*', ' ', processed_text)
    processed_text = re.sub(r'[^\w\s-]', ' ', processed_text) # Keeps letters, numbers, whitespace, hyphen
    processed_text = processed_text.replace('_', ' ')
    processed_text = ' '.join(processed_text.split())
    return processed_text.strip()

def load_pdf_field_details(filepath):
    """Loads PDF field details from i485_field_details.csv."""
    pdf_fields = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tooltip = row.get('PDF Field Label (from Tooltip)', '')
                pdf_fields.append({
                    'pdf_internal_id': row.get('PDF Internal ID', ''),
                    'pdf_tooltip_original': tooltip,
                    'extracted_pdf_item_labels': extract_item_labels_from_tooltip(tooltip),
                    'norm_pdf_tooltip_desc': normalize_text_for_comparison(tooltip)
                })
    except FileNotFoundError:
        print(f"Error: PDF details file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error reading PDF details CSV {filepath}: {e}")
        return None
    return pdf_fields

def load_simple_map_data(filepath):
    """Loads relevant data from the 'Fields Matched' section of simple_map.csv."""
    simple_map_entries = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            in_matched_section_header_found = False
            data_header_indices = {}

            for row_list in reader:
                if not any(field.strip() for field in row_list): 
                    in_matched_section_header_found = False 
                    data_header_indices = {}
                    continue

                if row_list[0].strip() == 'Section Header':
                    in_matched_section_header_found = False 
                    data_header_indices = {}
                    if len(row_list) > 1 and row_list[1].strip().startswith('Fields Matched'):
                        pass 
                    continue
                
                if not data_header_indices: 
                    if (len(row_list) > 3 and # Check for at least 4 columns for the main ones
                        row_list[0].strip() == 'I-485 Label' and 
                        'I-485 Field (Original)' in row_list and 
                        'I-485 Field (Normalized)' in row_list and 
                        'Jira Matches (Name - ID)' in row_list):
                        header = [h.strip() for h in row_list]
                        try:
                            data_header_indices['label'] = header.index('I-485 Label')
                            data_header_indices['field_original'] = header.index('I-485 Field (Original)')
                            data_header_indices['field_normalized'] = header.index('I-485 Field (Normalized)') 
                            data_header_indices['jira_matches'] = header.index('Jira Matches (Name - ID)')
                            in_matched_section_header_found = True 
                        except ValueError:
                            # print(f"Warning: Expected headers not found in a data section of {filepath}")
                            data_header_indices = {} 
                        continue 
                
                if in_matched_section_header_found and data_header_indices:
                    try:
                        i485_label = row_list[data_header_indices['label']].strip()
                        i485_field_original = row_list[data_header_indices['field_original']].strip()
                        i485_field_normalized = row_list[data_header_indices['field_normalized']].strip() 
                        jira_matches_str = row_list[data_header_indices['jira_matches']].strip()
                    except IndexError:
                        continue

                    if not i485_label and not i485_field_original: 
                        continue

                    parsed_jira_fields = []
                    if jira_matches_str:
                        for match_pair in jira_matches_str.split(';'):
                            match_pair = match_pair.strip()
                            if ' - ' in match_pair:
                                name, jira_id = match_pair.rsplit(' - ', 1)
                                parsed_jira_fields.append({
                                    'name': name.strip(), 
                                    'id': jira_id.strip(),
                                    'norm_name': normalize_text_for_comparison(name.strip())
                                })
                    
                    if parsed_jira_fields: 
                        simple_map_entries.append({
                            'i485_label_original': i485_label,
                            'i485_field_original': i485_field_original,
                            'i485_field_normalized': i485_field_normalized, 
                            'jira_fields': parsed_jira_fields,
                            'norm_i485_label': normalize_label_text(i485_label)
                        })
    except FileNotFoundError:
        print(f"Error: Simple map file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error reading simple map CSV {filepath}: {e}")
        return None
    return simple_map_entries

def main():
    pdf_details_filepath = '/Users/amyamylloyd/ImLaw/generalscripts/i485_field_details.csv'
    simple_map_filepath = '/Users/amyamylloyd/ImLaw/generalscripts/simple_map.csv'
    output_json_filepath = '/Users/amyamylloyd/ImLaw/generalscripts/i485_fill_map.json'

    pdf_fields = load_pdf_field_details(pdf_details_filepath)
    if pdf_fields is None:
        return

    simple_map_entries = load_simple_map_data(simple_map_filepath)
    if simple_map_entries is None:
        return
    
    if not simple_map_entries:
        print("No processable entries found in the 'Fields Matched' section of simple_map.csv with Jira data.")
        with open(output_json_filepath, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        print(f"Empty mapping written to {output_json_filepath}")
        return

    final_mappings = []
    pdf_fields_matched_count = 0

    for pdf_field in pdf_fields:
        if not pdf_field['pdf_internal_id']: 
            continue

        best_match_score = 0
        current_best_simple_map_entry = None

        for sm_entry in simple_map_entries:
            # Ensure 'i485_field_normalized' exists and is not empty
            i485_norm_desc_to_match = sm_entry.get('i485_field_normalized', '').strip()
            if not i485_norm_desc_to_match or not sm_entry.get('norm_i485_label', '').strip():
                continue 

            label_match = sm_entry['norm_i485_label'] in pdf_field['extracted_pdf_item_labels']
            
            desc_match = False
            # Compare the pre-normalized I-485 field from simple_map with the normalized PDF tooltip
            if i485_norm_desc_to_match in pdf_field['norm_pdf_tooltip_desc']:
                desc_match = True
            
            if label_match and desc_match:
                score = 100 + len(i485_norm_desc_to_match) 
                if score > best_match_score:
                    best_match_score = score
                    current_best_simple_map_entry = sm_entry
        
        if current_best_simple_map_entry:
            pdf_fields_matched_count +=1
            
            filtered_jira_sources = []
            # Target for Jira name matching is the pre-normalized I-485 field description from simple_map
            target_norm_desc_for_jira_match = current_best_simple_map_entry['i485_field_normalized']
            
            for jira_field_data in current_best_simple_map_entry['jira_fields']:
                if jira_field_data['norm_name'] == target_norm_desc_for_jira_match:
                    filtered_jira_sources.append({'name': jira_field_data['name'], 'id': jira_field_data['id']})
            
            if filtered_jira_sources: 
                final_mappings.append({
                    "pdf_internal_id": pdf_field['pdf_internal_id'],
                    "pdf_field_label_original": pdf_field['pdf_tooltip_original'],
                    "source_i485_label": current_best_simple_map_entry['i485_label_original'],
                    "source_i485_field_original": current_best_simple_map_entry['i485_field_original'],
                    "jira_source_fields": filtered_jira_sources 
                })

    print(f"Total PDF fields processed: {len(pdf_fields)}")
    print(f"Number of PDF fields successfully mapped to an I-485 entry with Jira data: {pdf_fields_matched_count}")
    
    try:
        with open(output_json_filepath, 'w', encoding='utf-8') as f:
            json.dump(final_mappings, f, indent=2)
        print(f"Successfully wrote field mappings to {output_json_filepath}")
    except Exception as e:
        print(f"Error writing JSON output to {output_json_filepath}: {e}")

if __name__ == '__main__':
    main()
