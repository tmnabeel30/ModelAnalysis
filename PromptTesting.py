import os
import json
import time
import re
from groq import Groq

# Configuration
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not set")
client = Groq(api_key=api_key)

model_name = "qwen-2.5-32b"
output_dir = "outputs"

def sanitize_filename(filename: str) -> str:
    """Sanitize the filename to remove invalid characters."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', filename)

def ensure_directory(path: str):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

def load_prompts_from_json(directory: str):
    """Load prompts from JSON files and maintain structure."""
    structured_prompts = {}
    
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' not found.")
    
    # Iterate through technique directories
    for technique in os.listdir(directory):
        technique_path = os.path.join(directory, technique)
        if os.path.isdir(technique_path):
            structured_prompts[technique] = {}
            
            # Iterate through category files
            for file in os.listdir(technique_path):
                if file.endswith(".json"):
                    file_path = os.path.join(technique_path, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        category = file.replace(".json", "")
                        prompts = data.get("prompts", [])
                        
                        if not isinstance(prompts, list):
                            raise ValueError(f"Invalid format in {file_path}, 'prompts' should be a list.")
                        
                        structured_prompts[technique][category] = prompts
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"Error reading {file_path}: {str(e)}")
    
    return structured_prompts

def query_model(prompt: str):
    """Query the LLM with the prompt and return the response as JSON."""
    try:
        # Modify the prompt to include JSON instruction
        modified_prompt = f"""Please provide your response as a JSON object. Here is the prompt:

{prompt}

Response should be in valid JSON format."""

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": modified_prompt}],
            temperature=0.7,
            response_format={"type": "json_object"},
            max_tokens=2000
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from model.")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from model."}
    except Exception as e:
        return {"error": str(e)}

def save_structured_response(technique: str, category: str, responses: list):
    """Save responses maintaining the directory structure."""
    # Create technique directory
    technique_dir = os.path.join(output_dir, sanitize_filename(technique))
    ensure_directory(technique_dir)
    
    # Save category responses
    output_filename = f"{sanitize_filename(category)}.json"
    output_path = os.path.join(technique_dir, output_filename)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(responses, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving file {output_path}: {str(e)}")

def main():
    # Create main output directory
    ensure_directory(output_dir)
    
    # Load structured prompts
    structured_prompts = load_prompts_from_json("Database of prompt")
    
    # Process prompts maintaining structure
    for technique, categories in structured_prompts.items():
        print(f"\nProcessing technique: {technique}")
        
        for category, prompts in categories.items():
            print(f"  Processing category: {category}")
            
            category_responses = []
            for prompt in prompts:
                response = query_model(prompt)
                category_responses.append({
                    "prompt": prompt,
                    "response": response
                })
                time.sleep(1.5)  # Rate limiting
            
            save_structured_response(technique, category, category_responses)

if __name__ == "__main__":
    try:
        main()
        print("\nProcessing complete. Check the outputs directory.")
    except Exception as e:
        print(f"Critical error: {str(e)}")