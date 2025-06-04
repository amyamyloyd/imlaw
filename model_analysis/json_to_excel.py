#!/usr/bin/env python3

"""
Convert complete analysis JSON to Excel table with specified columns.
"""

import os
import json
import pandas as pd
from datetime import datetime
import re

def extract_value_from_field_name(field_name: str) -> str:
    """Extract value from field name like 'Pt2Line10_State[0]' -> 'State'"""
    # Remove the [0] suffix first
    clean_name = re.sub(r'\[\d+\]$', '', field_name)
    
    # Extract after the last underscore
    if '_' in clean_name:
        return clean_name.split('_')[-1]
    
    # Fallback: return the clean name if no underscore
    return clean_name

def convert_json_to_excel(json_file_path: str) -> str:
    """Convert JSON analysis to Excel with specified columns"""
    print(f"Loading data from: {json_file_path}")
    
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} records to process")
    
    # Prepare data for DataFrame
    excel_data = []
    
    # Handle list format (data is a list of dictionaries)
    for field_data in data:
        field_name = field_data.get('name', '')
        
        # Extract value from field name
        value = extract_value_from_field_name(field_name)
        
        # Get value from value_info if available, otherwise use extracted value
        if field_data.get('value_info') and isinstance(field_data['value_info'], dict):
            value_from_info = field_data['value_info'].get('value')
            if value_from_info:
                value = str(value_from_info)
        
        # Prepare row data in specified order
        row = {
            'value': value,
            'name': field_name,
            'form': field_data.get('form', ''),
            'tooltip': field_data.get('tooltip', ''),
            'type': field_data.get('type', ''),
            'persona': field_data.get('persona', ''),
            'domain': field_data.get('domain', '')
        }
        
        excel_data.append(row)
    
    # Create DataFrame with specified column order
    df = pd.DataFrame(excel_data, columns=['value', 'name', 'form', 'tooltip', 'type', 'persona', 'domain'])
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.dirname(json_file_path)
    output_file = os.path.join(output_dir, f"complete_analysis_table_{timestamp}.xlsx")
    
    # Save to Excel
    print(f"Saving to Excel: {output_file}")
    
    # Use openpyxl engine for .xlsx format
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Form Fields Analysis', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Form Fields Analysis']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            # Set a reasonable max width
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"Excel file created successfully!")
    print(f"Records processed: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Show summary by form
    form_counts = df['form'].value_counts()
    print(f"\nRecords by form:")
    for form, count in form_counts.items():
        print(f"  {form}: {count} records")
    
    return output_file

def main():
    # Path to the complete analysis file
    json_file = "model_analysis/results/run_20250604_085938/complete_analysis_20250604_085938.json"
    
    if not os.path.exists(json_file):
        print(f"Error: File not found: {json_file}")
        print("Please check the file path.")
        return
    
    try:
        output_file = convert_json_to_excel(json_file)
        print(f"\n✅ Conversion completed successfully!")
        print(f"Output file: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 