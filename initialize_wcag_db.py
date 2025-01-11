#!/usr/bin/env python3
"""
Initialize the WCAG 2.2 vector store database.
This script should be run once before using the a11y checker.
"""

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
    
    print("Initializing WCAG 2.2 vector store...")
    
    # Remove existing database if it exists
    db_path = Path(".chroma_db")
    if db_path.exists():
        print("Removing existing database at .chroma_db")
        import shutil
        shutil.rmtree(db_path)
    
    print("Creating new vector store with WCAG 2.2 guidelines...")
    vs = WCAGVectorStore()
    vs.initialize_db(wcag_file="data/wcag_2_2_new.json")  # Use the new WCAG data file
    print("Vector store initialization complete!")

if __name__ == "__main__":
    main()
