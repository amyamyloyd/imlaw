import csv
import re

def normalize_for_comparison(text):
    """Simple normalization: lowercase and strip whitespace."""
    if not isinstance(text, str):
        return ""
    return text.lower().strip()

def count_i485_to_jira_name_matches(filepath):
    rows_with_name_match_count = 0
    rows_without_name_match_count = 0
    processed_data_rows = 0
    
    matched_records_details = []
    non_matched_records_details = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header_row = []
            original_col_idx = -1
            jira_matches_col_idx = -1
            
            in_relevant_section_data_header_found = False
            
            for row_num, row_list in enumerate(reader, 1): # Iterate through rows
                if not any(field.strip() for field in row_list): # Skip truly empty rows
                    in_relevant_section_data_header_found = False
                    header_row = []
                    continue

                if row_list[0].strip() == 'Section Header':
                    in_relevant_section_data_header_found = False
                    header_row = []
                    continue
            
                # Check for the data header row for "Fields Matched" or "Fields not Matched"
                if not in_relevant_section_data_header_found: # Try to find header if not already found
                    if (len(row_list) > 0 and row_list[0].strip() == 'I-485 Label' and
                        'I-485 Field (Original)' in row_list and
                        'Jira Matches (Name - ID)' in row_list):
                        
                        header_row = [h.strip() for h in row_list]
                        try:
                            original_col_idx = header_row.index('I-485 Field (Original)')
                            jira_matches_col_idx = header_row.index('Jira Matches (Name - ID)')
                            in_relevant_section_data_header_found = True
                        except ValueError:
                            header_row = [] # Reset if headers are not as expected
                            in_relevant_section_data_header_found = False
                        continue # Processed header (or failed), move to next row
                
                if in_relevant_section_data_header_found and header_row:
                    # This is a data row within a relevant section
                    try:
                        original_field = row_list[original_col_idx].strip()
                        jira_matches_str = row_list[jira_matches_col_idx].strip()
                        processed_data_rows += 1
                        
                        found_a_match_in_row = False
                        matching_jira_name_part_for_log = ""
                        if original_field and jira_matches_str: # Only proceed if both have content
                            norm_original_field = normalize_for_comparison(original_field)
                            
                            individual_jira_matches = jira_matches_str.split(';')
                            for jira_match_item in individual_jira_matches:
                                jira_match_item = jira_match_item.strip()
                                if ' - ' in jira_match_item:
                                    # Get the name part before the " - customfield_XXXXX"
                                    jira_name_with_prefix = jira_match_item.rsplit(' - ', 1)[0]
                                    
                                    # If there's a colon, take the part after it
                                    if ':' in jira_name_with_prefix:
                                        jira_name_part = jira_name_with_prefix.split(':', 1)[1].strip()
                                    else:
                                        jira_name_part = jira_name_with_prefix.strip()
                                        
                                    norm_jira_name_part = normalize_for_comparison(jira_name_part)
                                    
                                    if norm_original_field == norm_jira_name_part:
                                        found_a_match_in_row = True
                                        matching_jira_name_part_for_log = jira_name_part
                                        break # Found a match for this row, no need to check other Jira items
                        
                        if found_a_match_in_row:
                            rows_with_name_match_count += 1
                            matched_records_details.append({
                                "row_number_in_simple_map": row_num,
                                "i485_original_field": original_field,
                                "jira_matches_string": jira_matches_str,
                                "matched_jira_name": matching_jira_name_part_for_log
                            })
                        else:
                            rows_without_name_match_count += 1
                            non_matched_records_details.append({
                                "row_number_in_simple_map": row_num,
                                "i485_original_field": original_field,
                                "jira_matches_string": jira_matches_str
                            })
                            # Optional: print rows that don't match for debugging
                            # print(f"Row {row_num} - No direct name match: I-485 Original='{original_field}', Jira String='{jira_matches_str}'")




                    except IndexError:
                        # Row doesn't have enough columns for the expected header
                        # print(f"Skipping malformed data row {row_num} in {filepath}: {row_list}")
                        continue
                        
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None, None, None, None, None # Adjusted return for error
    except Exception as e:
        print(f"Error reading CSV {filepath}: {e}")
        return None, None, None, None, None # Adjusted return for error
    return rows_with_name_match_count, rows_without_name_match_count, processed_data_rows, matched_records_details, non_matched_records_details

def write_details_to_csv(output_csv_path, matched_details, non_matched_details):
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)

            # Matched Records Section
            writer.writerow(["Section", "Row in simple_map.csv", "I-485 Field (Original)", "Jira Matches (Full String)", "Specifically Matched Jira Name"])
            if matched_details:
                for record in matched_details:
                    writer.writerow([
                        "Matched",
                        record["row_number_in_simple_map"],
                        record["i485_original_field"],
                        record["jira_matches_string"],
                        record["matched_jira_name"]
                    ])
            
            writer.writerow([]) # Blank separator row

            # Non-Matched Records Section
            writer.writerow(["Section", "Row in simple_map.csv", "I-485 Field (Original)", "Jira Matches (Full String)", "Specifically Matched Jira Name"])
            if non_matched_details:
                for record in non_matched_details:
                    writer.writerow([
                        "Not Matched",
                        record["row_number_in_simple_map"],
                        record["i485_original_field"],
                        record["jira_matches_string"],
                        "" # No specific match
                    ])
        print(f"Detailed comparison results written to {output_csv_path}")
    except Exception as e:
        print(f"Error writing details to CSV {output_csv_path}: {e}")

if __name__ == '__main__':
    simple_map_file = '/Users/amyamylloyd/ImLaw/generalscripts/simple_map.csv'
    output_details_csv = '/Users/amyamylloyd/ImLaw/generalscripts/checkmap_details_output.csv'
    
    results = count_i485_to_jira_name_matches(simple_map_file)
    
    if results[0] is not None: # Check if the first count is not None (indicates successful processing)
        match_count, no_match_count, total_data_rows, matched_details, non_matched_details = results
        print(f"Comparison of 'I-485 Field (Original)' with Jira field names in {simple_map_file}:")
        print(f"Total data rows processed in 'Fields Matched' section: {total_data_rows}")
        print(f"Number of rows where 'I-485 Field (Original)' matches at least one Jira field name: {match_count}")
        print(f"Number of rows where 'I-485 Field (Original)' does NOT match any Jira field name: {no_match_count}")
        
        write_details_to_csv(output_details_csv, matched_details, non_matched_details)
    else:
        print("Could not process the file.")
