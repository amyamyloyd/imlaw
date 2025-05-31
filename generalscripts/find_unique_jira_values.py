import json

def analyze_fill_map_jira_ids(json_filepath):
    """
    Analyzes the i485_fill_map.json to find unique Jira IDs.
    """
    unique_jira_ids = set()
    
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            fill_map_data = json.load(f)
            
            if not isinstance(fill_map_data, list):
                print(f"Error: Expected a list of records in {json_filepath}, but found {type(fill_map_data)}")
                return None, None
                
            for record in fill_map_data:
                jira_sources = record.get("jira_source_fields", [])
                if isinstance(jira_sources, list):
                    for jira_field in jira_sources:
                        if isinstance(jira_field, dict) and "id" in jira_field:
                            unique_jira_ids.add(jira_field["id"])
                else:
                    print(f"Warning: 'jira_source_fields' in record is not a list: {record.get('pdf_internal_id', 'Unknown PDF ID')}")

    except FileNotFoundError:
        print(f"Error: File not found at {json_filepath}")
        return None, None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_filepath}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None
        
    return len(unique_jira_ids), sorted(list(unique_jira_ids))

if __name__ == '__main__':
    fill_map_path = '/Users/amyamylloyd/ImLaw/generalscripts/i485_fill_map.json'
    count, ids = analyze_fill_map_jira_ids(fill_map_path)
    
    if count is not None:
        print(f"Found {count} unique Jira IDs in '{fill_map_path}':")
        if ids:
            for jira_id in ids:
                print(f"- {jira_id}")
        else:
            print("No Jira IDs found.")
