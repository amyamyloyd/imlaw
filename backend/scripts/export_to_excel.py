"""
Script to export field tooltips table to an Excel file.
"""

import pandas as pd
import json
import os

def create_excel():
    # Read the field tooltips data
    with open('/Users/claudiapitts/imlaw/Imlaw/generalscripts/field_analysis/complete_analysis.json', 'r') as f:
        all_forms_data = json.load(f)
    
    # Create list to hold all rows
    table_data = []
    
    # Collect data for each field
    for form_name, form_data in all_forms_data.items():
        for field in form_data['fields']:
            if field.get('tooltip'):  # Only include fields with tooltips
                # Clean up tooltip text - remove extra whitespace and newlines
                tooltip = ' '.join(field.get('tooltip', '').split())
                table_data.append({
                    'Form': form_name,
                    'Tooltip': tooltip,
                    'Field Name': field.get('name', ''),
                    'Field Type': field.get('type', ''),
                    'Page': field.get('page', '')
                })
    
    # Convert to DataFrame and sort
    df = pd.DataFrame(table_data)
    df = df.sort_values(by=['Form', 'Tooltip', 'Field Name'])
    
    # Create Excel writer with formatting
    output_file = '/Users/claudiapitts/imlaw/Imlaw/generalscripts/field_analysis/field_tooltips.xlsx'
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Field Analysis', index=False)
        
        # Get workbook and worksheet objects for formatting
        workbook = writer.book
        worksheet = writer.sheets['Field Analysis']
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'text_wrap': True,
            'border': 1
        })
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Form
        worksheet.set_column('B:B', 60)  # Tooltip
        worksheet.set_column('C:C', 30)  # Field Name
        worksheet.set_column('D:D', 15)  # Field Type
        worksheet.set_column('E:E', 10)  # Page
        
        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Apply cell format to all data cells
        for row in range(1, len(df) + 1):
            for col in range(len(df.columns)):
                worksheet.write(row, col, df.iloc[row-1, col], cell_format)
        
        # Add autofilter
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
        
        # Freeze the header row
        worksheet.freeze_panes(1, 0)
    
    print(f'\nExcel file created successfully at: {output_file}')
    print(f'Total fields with tooltips: {len(df)}')

if __name__ == '__main__':
    create_excel() 