import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, List, Optional
import time

def get_techniques_and_failures(client: OpenAI, ref_id: str, title: str, description: str, guideline_description: str = "", special_cases: List[str] = None) -> tuple[List[str], List[str]]:
    """
    Use OpenAI to generate relevant techniques and failures for a WCAG criterion.
    Rate limits requests to avoid hitting OpenAI's rate limits.
    """
    print(f"\nGenerating content for {ref_id} - {title}")
    print(f"Description: {description[:100]}...")
    
    # Build context with guideline description and special cases
    context = f"Guideline Context: {guideline_description}\n" if guideline_description else ""
    if special_cases:
        context += "\nSpecial Cases:\n" + "\n".join(f"- {case}" for case in special_cases)
    
    prompt = f"""You are a WCAG accessibility expert. For the following WCAG criterion:

ID: {ref_id}
Title: {title}
Description: {description}
{context}

Please provide:
1. A list of 4-6 specific, actionable techniques for implementing this criterion in web applications
2. A list of 3-5 common failures or mistakes that violate this criterion

Format your response exactly like this example:
TECHNIQUES
- Use semantic HTML elements for structure
- Implement proper ARIA labels
- Ensure keyboard focus indicators are visible

FAILURES
- Using color alone to convey information
- Not providing alternative text for images
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a WCAG accessibility expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=700
        )
        
        # Parse response
        content = response.choices[0].message.content
        techniques = []
        failures = []
        
        current_list = None
        for line in content.split('\n'):
            line = line.strip()
            if line == 'TECHNIQUES':
                current_list = techniques
            elif line == 'FAILURES':
                current_list = failures
            elif line.startswith('- '):
                if current_list is not None:
                    current_list.append(line[2:])
        
        print("\nGenerated content:")
        print("Techniques:")
        for t in techniques:
            print(f"  - {t}")
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
        
        # Sleep to avoid rate limits (1 second between requests)
        print("\nWaiting a second before next request...")
        time.sleep(1)
        
        return techniques, failures
    except Exception as e:
        print(f"Error generating content for {ref_id}: {str(e)}")
        return [], []

def extract_success_criteria(data: List[Dict]) -> List[Dict]:
    """Extract all success criteria from the old WCAG format"""
    criteria = []
    
    for principle in data:
        for guideline in principle["guidelines"]:
            guideline_description = guideline.get("description", "")
            for criterion in guideline.get("success_criteria", []):
                criteria.append({
                    "name": f"{criterion['ref_id']} {criterion['title']}",
                    "level": criterion["level"],  # Use level directly from source
                    "description": criterion["description"],
                    "url": criterion.get("url", f"https://www.w3.org/WAI/WCAG22/Understanding/{criterion['ref_id'].lower()}.html"),
                    "guideline_description": guideline_description,
                    "special_cases": criterion.get("special_cases", [])
                })
    
    return criteria

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize OpenAI client
    client = OpenAI()
    
    # Load old WCAG data
    with open("data/wcag.json", "r") as f:
        old_data = json.load(f)
    
    # Extract success criteria
    criteria = extract_success_criteria(old_data)
    
    # Generate techniques and failures for each criterion
    print(f"Generating techniques and failures for {len(criteria)} criteria...")
    for criterion in criteria:
        print(f"Processing {criterion['name']}...")
        print(f"Guideline Context: {criterion['guideline_description']}")
        if criterion['special_cases']:
            print("Special Cases:")
            for case in criterion['special_cases']:
                print(f"  - {case}")
                
        techniques, failures = get_techniques_and_failures(
            client,
            criterion['name'].split()[0],  # ref_id
            " ".join(criterion['name'].split()[1:]),  # title
            criterion['description'],
            criterion['guideline_description'],
            criterion['special_cases']
        )
        criterion['techniques'] = techniques
        criterion['failures'] = failures
    
    # Create new format
    new_data = {
        "guidelines": criteria
    }
    
    # Save new format
    with open("data/wcag_2_2_new.json", "w") as f:
        json.dump(new_data, f, indent=4)
    
    print("Transformation complete! New file saved as data/wcag_2_2_new.json")

if __name__ == "__main__":
    main()
