import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import time

def get_techniques_and_failures(client: OpenAI, ref_id: str, title: str, description: str, guideline_description: str = "", special_cases: List[str] = None) -> Tuple[str, List[str], List[str]]:
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
1. A clear, concise description of this criterion that focuses on its core requirements and purpose, without mentioning implementation techniques or failures.
2. A list of 4-6 specific, actionable techniques for implementing this criterion in web applications
3. A list of 3-5 common failures or mistakes that violate this criterion

Format your response exactly like this example:
DESCRIPTION
This criterion ensures that all non-text content has a text alternative that serves an equivalent purpose, enabling users with visual impairments to understand the content through screen readers or other assistive technologies.

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
        description = ""
        techniques = []
        failures = []
        
        current_section = None
        description_lines = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line == 'DESCRIPTION':
                current_section = 'description'
            elif line == 'TECHNIQUES':
                current_section = 'techniques'
            elif line == 'FAILURES':
                current_section = 'failures'
            elif line:
                if current_section == 'description':
                    description_lines.append(line)
                elif current_section == 'techniques' and line.startswith('- '):
                    techniques.append(line[2:])
                elif current_section == 'failures' and line.startswith('- '):
                    failures.append(line[2:])
        
        description = ' '.join(description_lines)
        
        print("\nGenerated content:")
        print("Description:", description)
        print("\nTechniques:")
        for t in techniques:
            print(f"  - {t}")
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
        
        # Sleep to avoid rate limits (1 second between requests)
        print("\nWaiting a second before next request...")
        time.sleep(1)
        
        return description, techniques, failures
    except Exception as e:
        print(f"Error generating content for {ref_id}: {str(e)}")
        return "", [], []

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
    # Load environment variables from .env file
    load_dotenv()
    
    # Initialize OpenAI client
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    client = OpenAI(api_key=openai_api_key)
    
    # Load original WCAG data
    with open("data/wcag.json", "r") as f:
        data = json.load(f)
    
    # Extract success criteria
    criteria = extract_success_criteria(data)
    
    # Generate techniques and failures for each criterion
    guidelines = []
    for criterion in criteria:
        name = criterion["name"]
        ref_id = name.split(" ")[0]
        title = " ".join(name.split(" ")[1:])
        
        description, techniques, failures = get_techniques_and_failures(
            client,
            ref_id,
            title,
            criterion["description"],
            criterion["guideline_description"],
            criterion.get("special_cases", [])
        )
        
        guidelines.append({
            "name": name,
            "level": criterion["level"],
            "description": description or criterion["description"],  # Fall back to original if generation fails
            "url": criterion["url"],
            "techniques": techniques,
            "failures": failures
        })
    
    # Save transformed data
    output = {
        "guidelines": guidelines
    }
    
    with open("data/wcag_2_2_new.json", "w") as f:
        json.dump(output, f, indent=4)
    
    print("\nTransformation complete! New data saved to data/wcag_2_2_new.json")

if __name__ == "__main__":
    main()
