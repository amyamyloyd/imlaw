import os
import sys
import json
import glob
import time
import re
from datetime import datetime
import openai

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY environment variable is not set. Please set it and rerun the script.")
    sys.exit(1)
openai.api_key = api_key

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
BATCH_SIZE = 10

def get_latest_analysis_file():
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "run_*/complete_analysis_*.json")), reverse=True)
    return files[0] if files else None

def get_latest_value_mapped_file():
    files = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "value_mapping/value_mapping_*.json")), reverse=True)
    return files[0] if files else None

def is_label_only_tooltip(field):
    tooltip = field.get("tooltip", "")
    name = field.get("name", "")
    if not tooltip or tooltip.strip() == "" or tooltip.strip() == name:
        return True
    if len(tooltip.strip()) < 8:
        return True
    if re.fullmatch(r'[\w\[\]0-9]+', tooltip.strip()):
        return True
    return False

def build_batch_prompt(fields):
    instructions = '''
You are an expert in immigration form field classification. For each field, use the tooltip as the primary source to determine:
- persona: Who does this field apply to? (choose the closest match from: applicant, beneficiary, spouse, parent, preparer, attorney, employer, interpreter, family_member, physician, sponsor; if unsure, pick the most likely based on the tooltip and context, and if truly ambiguous, default to 'applicant')
- domain: What type of data is this? (e.g., personal, medical, criminal, immigration, office, etc.)
- react_label: A concise, user-friendly label for this field, suitable for a React UI (avoid technical jargon, use plain English).

Rules:
- The tooltip describes who is the subject of the question—typically the petitioner/applicant, their family members, their beneficiaries, the beneficiaries' family members, or employment-related parties.
- Use the tooltip as the main source for persona and domain.
- Use the form name and field name for additional context.
- If the tooltip contains: "beneficiary" → persona = beneficiary
- If the tooltip contains: "your child" or "your children" → persona = family_member
- If the tooltip contains: "spouse" → persona = spouse
- If the tooltip contains: "father", "mother", or "parent" → persona = parent
- If the tooltip contains: "preparer" → persona = preparer
- If the tooltip contains: "employer" → persona = employer
- If the tooltip contains: "interpreter" → persona = interpreter
- If the tooltip contains: "attorney" → persona = attorney
- If the tooltip contains: "physician", "doctor", or "civil surgeon" → persona = physician
- If the tooltip contains: "sponsor" → persona = sponsor
- If the tooltip contains: "applicant", "you", or "your" (and does NOT refer to child, spouse, parent, etc.) → persona = applicant
- If the tooltip contains: "family" (and does NOT include beneficiary, spouse, parent) → persona = family
- Use form part mappings if available (e.g., Pt9 in i485.pdf is always interpreter).
- For domain, use these patterns:
  - personal: name, DOB, place of birth, SSN, address, phone, marital status, gender, race, etc.
  - medical: medical, health, exam, vaccine, treatment, diagnosis, doctor, physician, hospital, disability, immunization, mental, drug, etc.
  - criminal: criminal, arrest, conviction, offense, prison, court, police, felony, violation, illegal, etc.
  - immigration: alien number, I94, passport, visa, status, deportation, asylum, citizenship, etc.
  - office: receipt, filing, office, administrative, form, signature, fee, preparer, attorney, representative, etc.
- Overrides:
  - If persona is preparer/attorney → domain is office.
  - If tooltip contains "lawful" and persona is applicant → domain is personal.
  - If tooltip contains "inadmissibility" → domain is criminal.
  - If tooltip contains "address" or "street" → domain is personal (never medical).
  - If the field name or tooltip contains "PDF417BarCode" or is a barcode, set persona=attorney and domain=office.
  - For vaccination or medical records, persona=applicant unless the tooltip specifically says beneficiary, then persona=beneficiary.
  - If the tooltip says "This is a read only field. This field pre-populates from page", set persona=applicant.
- Tooltips may reference historical data (e.g., previous addresses, past employers).
- Medical questions often ask about vaccines, doctor clearances, or dates.
- The same field label (like "Name") may apply to different personas in different sections or forms.
- If the tooltip is ambiguous, use the form part or section if available.
- Respond with a JSON array, one object per field, in the same order as the input.
- Each object must have: persona, domain, react_label.

Examples:
1. {"form": "i485.pdf", "name": "Pt9Line2_InterpreterGivenName[0]", "type": "/Tx", "tooltip": "Interpreter's Given Name. Enter the interpreter's first name."}
   Output: {"persona": "interpreter", "domain": "office", "react_label": "Interpreter's First Name"}
2. {"form": "i693.pdf", "name": "Pt4Line5_VaccineDate[0]", "type": "/Tx", "tooltip": "Date of last tetanus vaccine. Enter the date."}
   Output: {"persona": "applicant", "domain": "medical", "react_label": "Date of Last Tetanus Vaccine"}
3. {"form": "i130.pdf", "name": "Pt2Line10_PreviousEmployer[0]", "type": "/Tx", "tooltip": "Previous employer's name. Enter the name of your previous employer."}
   Output: {"persona": "applicant", "domain": "personal", "react_label": "Previous Employer Name"}
4. {"form": "i485.pdf", "name": "PDF417BarCode1[0]", "type": "/Tx", "tooltip": "PDF417BarCode1"}
   Output: {"persona": "attorney", "domain": "office", "react_label": "Barcode"}
5. {"form": "i693.pdf", "name": "Pt4Line5_VaccineDate[0]", "type": "/Tx", "tooltip": "This is a read only field. This field pre-populates from page 2."}
   Output: {"persona": "applicant", "domain": "medical", "react_label": "Pre-populated Vaccine Date"}
'''
    # Build the input array
    field_jsons = []
    for field in fields:
        field_jsons.append({
            "form": field.get("form", ""),
            "name": field.get("name", ""),
            "type": field.get("type", ""),
            "tooltip": field.get("tooltip", "")
        })
    prompt = f"{instructions}\nInput fields:\n{json.dumps(field_jsons, ensure_ascii=False)}\n\nRespond with a JSON array of objects, one per field, in the same order."
    return prompt

def enrich_fields_with_llm_batch(fields, model="gpt-4-turbo"):
    prompt = build_batch_prompt(fields)
    print(f"Batch prompt for fields {fields[0].get('name')} ... {fields[-1].get('name')}")
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        print(f"Raw LLM batch response: {content[:500]}...\n")
        try:
            results = json.loads(content)
            if not isinstance(results, list) or len(results) != len(fields):
                raise ValueError("LLM batch response is not a list of correct length.")
            for field, result in zip(fields, results):
                field["llm_persona"] = result.get("persona")
                field["llm_domain"] = result.get("domain")
                field["react_label"] = result.get("react_label")
        except Exception as e:
            print(f"JSON decode error for batch: {e}")
            for field in fields:
                field["llm_persona"] = None
                field["llm_domain"] = None
                field["react_label"] = None
    except Exception as e:
        print(f"LLM error for batch: {e}")
        for field in fields:
            field["llm_persona"] = None
            field["llm_domain"] = None
            field["react_label"] = None
    return fields

def build_collection_prompt(fields):
    instructions = '''
You are an expert in data modeling for immigration forms. Given the following list of form fields (with persona, domain, value, tooltip, etc.), group them into canonical collection fields. For each collection field, specify:
- collection_field_name: a clear, consistent canonical name (e.g., applicant_given_name, beneficiary_employer_name)
- type: text, selection, boolean, etc.
- persona
- domain
- value
- isrepeating: "y" if this is a repeating/collection field (e.g., employment history, address history, family members), "n" otherwise
- fields: an array of all mapped form fields (with form, name, tooltip, screen_label, value, etc.)

Only use fields where both persona and value are non-null. Use field name patterns and tooltips to infer repeating/collection fields (e.g., Employer 1, Employer 2, history, previous, etc.).

Output a JSON array as described. At the end, provide a human-readable summary of the collection fields and their mappings.
'''
    # Only include fields with non-null persona and value
    filtered = [
        {
            "form": f.get("form"),
            "name": f.get("name"),
            "type": f.get("type"),
            "persona": f.get("persona"),
            "domain": f.get("domain"),
            "value": (f.get("value_info") or {}).get("value"),
            "tooltip": f.get("tooltip"),
            "screen_label": f.get("screen_label")
        }
        for f in fields if f.get("persona") and (f.get("value_info") or {}).get("value")
    ]
    prompt = f"{instructions}\nInput fields:\n{json.dumps(filtered, ensure_ascii=False)}\n\nRespond with a JSON array of collection fields as described."
    return prompt

def group_fields_with_llm(fields, model="gpt-4-turbo"):
    prompt = build_collection_prompt(fields)
    print(f"Sending {len(fields)} fields to LLM for collection field grouping...")
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        print(f"Raw LLM response (first 1000 chars): {content[:1000]}\n...")
        try:
            results = json.loads(content)
            return results
        except Exception as e:
            print(f"JSON decode error for collection fields: {e}")
            return None
    except Exception as e:
        print(f"LLM error for collection fields: {e}")
        return None

def main():
    latest_file = get_latest_value_mapped_file()
    if not latest_file:
        print("No value_mapping_*.json file found.")
        return
    print(f"Reading: {latest_file}")
    with open(latest_file, "r") as f:
        all_fields = json.load(f)
    # Only use fields with non-null persona and value
    filtered_fields = [f for f in all_fields if f.get("persona") and (f.get("value_info") or {}).get("value")]
    print(f"Grouping {len(filtered_fields)} fields into collection fields with LLM...")
    if len(filtered_fields) > 2000:
        print("WARNING: Too many fields for a single LLM call. Consider splitting the data.")
        return
    collection_fields = group_fields_with_llm(filtered_fields)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(os.path.dirname(latest_file), f"collection_fields_{timestamp}.json")
    if collection_fields:
        with open(out_file, "w") as f:
            json.dump(collection_fields, f, indent=2)
        print(f"Wrote collection fields to: {out_file}")
    else:
        print("No collection fields output.")

if __name__ == "__main__":
    main() 