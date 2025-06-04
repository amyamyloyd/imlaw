import os
import json
import glob
from datetime import datetime
import openai

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY environment variable is not set. Please set it and rerun the script.")
    exit(1)
openai.api_key = api_key

LLM_BATCH_DIR = "model_analysis/llm_batches"
MODEL = "gpt-4-turbo"
MAX_RECORDS = 2000  # safety limit

PROMPT_TEMPLATE = '''
You are an expert in data modeling for immigration forms. Given the following list of form fields (with persona, domain, value, screen_label, etc.), group them into canonical collection fields. For each collection field, specify:
- collection_field_name: a clear, consistent canonical name (e.g., applicant_given_name, beneficiary_employer_name)
- type: text, selection, boolean, etc.
- persona
- domain
- isrepeating: "y" if this is a repeating/collection field (e.g., employment history, address history, family members), "n" otherwise
- fields: an array of all mapped form fields (with all available metadata: name, type, persona, domain, value, screen_label)

Instructions:
- Group fields that represent the same data for the persona, even if they appear in different forms or as repeating groups.
- Propose a clear, consistent naming convention for collection fields.
- Mark collection fields as isrepeating: y/n if they represent repeating data (e.g., employment history).
- For each collection field, include an array of all mapped form fields with all available metadata.
- Only use fields with non-null value and persona.
- If unsure, err on the side of grouping more fields together (to avoid fragmentation).
- Output a JSON array of collection fields, each with: collection_field_name, type, persona, domain, isrepeating, fields (array of mapped form fields with all metadata).

Input fields:
{fields_json}

Respond with a JSON array of collection fields as described.
'''

def run_llm_collection_model(fields):
    prompt = PROMPT_TEMPLATE.format(fields_json=json.dumps(fields, ensure_ascii=False))
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        try:
            results = json.loads(content)
            return results
        except Exception as e:
            print(f"JSON decode error: {e}\nRaw LLM output:\n{content[:1000]}\n...")
            return None
    except Exception as e:
        print(f"LLM error: {e}")
        return None

def main():
    files = sorted(glob.glob(os.path.join(LLM_BATCH_DIR, "*_llm.json")))
    for fpath in files:
        persona = os.path.basename(fpath).replace("_llm.json", "")
        print(f"Processing persona: {persona}")
        with open(fpath, "r") as f:
            fields = json.load(f)
        # Filter to non-null value and persona
        filtered = [rec for rec in fields if rec.get("persona") and rec.get("value")]
        print(f"  {len(filtered)} fields to model.")
        if len(filtered) > MAX_RECORDS:
            print(f"  SKIPPED: Too many records for LLM ({len(filtered)} > {MAX_RECORDS})")
            continue
        results = run_llm_collection_model(filtered)
        out_file = os.path.join(LLM_BATCH_DIR, f"{persona}_collection_model.json")
        if results:
            with open(out_file, "w") as f:
                json.dump(results, f, indent=2)
            print(f"  Wrote collection model to {out_file}")
        else:
            print(f"  No output for {persona}")

if __name__ == "__main__":
    main() 