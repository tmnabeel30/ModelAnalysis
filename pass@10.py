import openai
import os
import json
import pandas as pd
import time

# 🔑 Set your API key here
openai.api_key = "your-api-key-here"

BASE_DIR = "Database of prompt"  # root folder path

def load_prompts_from_all_jsons(base_dir):
    prompt_entries = []

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".json"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    try:
                        data = json.load(f)
                        attack_type = data.get("Attack Type", os.path.basename(root))
                        subcategory = data.get("Subcategory", os.path.splitext(file)[0])

                        for item in data.get("Prompts", []):
                            prompt_text = item["prompt"]
                            prompt_entries.append({
                                "Attack Type": attack_type,
                                "Subcategory": subcategory,
                                "Prompt": prompt_text
                            })
                    except Exception as e:
                        print(f"❌ Failed to load {filepath}: {e}")
    
    return prompt_entries

def get_pass10_responses(prompt, n=10, model="gpt-4", max_tokens=200):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            n=n,
            temperature=1.0,
            max_tokens=max_tokens
        )
        return [choice.message.content for choice in response.choices]
    except Exception as e:
        print(f"❌ Error fetching response for: {prompt[:50]}... | Error: {e}")
        return ["ERROR"] * n

def build_response_dataframe(prompt_entries):
    all_rows = []
    for i, entry in enumerate(prompt_entries):
        print(f"🔄 [{i+1}/{len(prompt_entries)}] Processing prompt: {entry['Prompt'][:50]}...")
        responses = get_pass10_responses(entry["Prompt"])

        row = {
            "Attack Type": entry["Attack Type"],
            "Subcategory": entry["Subcategory"],
            "Prompt": entry["Prompt"]
        }

        for j, response in enumerate(responses, 1):
            row[f"Response {j}"] = response

        all_rows.append(row)
        time.sleep(1)  # to avoid hitting rate limits

    return pd.DataFrame(all_rows)

def main():
    print("📥 Loading prompts...")
    prompt_entries = load_prompts_from_all_jsons(BASE_DIR)
    
    print("🚀 Generating responses...")
    df = build_response_dataframe(prompt_entries)
    
    print("💾 Saving to Excel...")
    df.to_excel("jailbreak_pass10_results.xlsx", index=False)
    print("✅ Done: Saved to 'jailbreak_pass10_results.xlsx'")

if __name__ == "__main__":
    main()
