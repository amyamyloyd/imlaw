#!/usr/bin/env python3

import json
import os
import re

def fix_json_file(input_file, output_file):
    print(f"Reading {input_file}...")
    with open(input_file, 'r') as f:
        content = f.read()
    
    print("Fixing JSON structure...")
    
    # Basic cleanup
    content = content.strip()
    
    # Ensure array structure
    if not content.startswith('['):
        content = '[' + content
    if not content.endswith(']'):
        content = content + ']'
    
    # Fix common issues
    content = content.replace('}{', '},{')  # Add missing commas between objects
    content = content.replace(',]', ']')    # Remove trailing commas in arrays
    content = content.replace(',}', '}')    # Remove trailing commas in objects
    content = content.replace(',,', ',')    # Remove double commas
    content = content.replace('null', '"null"')  # Quote null values
    content = content.replace('undefined', '"undefined"')  # Quote undefined values
    
    print(f"Writing fixed JSON to {output_file}...")
    with open(output_file, 'w') as f:
        f.write(content)
    print("Done!")

def main():
    analysis_dir = "backend/field_analysis"
    latest_results = max(
        [d for d in os.listdir(analysis_dir) if d.startswith('analysis_results_')],
        key=lambda x: x.split('_')[2:]
    )
    
    input_file = os.path.join(analysis_dir, latest_results, f"field_analysis_results_{latest_results.split('_', 2)[2]}.json")
    output_file = os.path.join(analysis_dir, latest_results, f"field_analysis_results_{latest_results.split('_', 2)[2]}_fixed.json")
    
    if fix_json_file(input_file, output_file):
        # If fix was successful, replace the original file
        os.rename(output_file, input_file)
        print("Original file updated successfully!")
    else:
        print("Failed to fix JSON. Check the output file for details.")

if __name__ == "__main__":
    main() 