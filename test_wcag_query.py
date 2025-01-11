#!/usr/bin/env python3
"""Test script for querying the WCAG vector store"""

import os
from pathlib import Path
from dotenv import load_dotenv
from crew.wcag_rag import WCAGVectorStore

def main():
    # Load environment variables from .env file
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in .env file")
    
    print("Testing WCAG vector store query...")
    vs = WCAGVectorStore()
    
    # Test query about image accessibility
    query = """
    I need to provide alternative text for an image that shows a chart with important company revenue data. 
    What are the WCAG requirements for making this chart accessible to screen reader users?
    """
    
    print("\nQuery:", query)
    print("\nResults:")
    results = vs.query_similar_guidelines(query, k=3)
    
    for i, result in enumerate(results, 1):
        guideline = result['guideline']
        score = result['score']
        print(f"\n{i}. {guideline.ref_id} - {guideline.title} (Score: {score:.3f})")
        print("   Techniques:")
        for technique in guideline.techniques:
            print(f"   - {technique}")
        print("   Failures:")
        for failure in guideline.failures:
            print(f"   - {failure}")
        print("\n   Description:", guideline.description)

if __name__ == "__main__":
    main()
