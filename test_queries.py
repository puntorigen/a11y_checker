from crew.wcag_rag import WCAGVectorStore
from dotenv import load_dotenv
import os

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize vector store
    vs = WCAGVectorStore()
    
    # Test queries
    test_queries = [
        "What are the requirements for color contrast?",
        "How should I handle keyboard navigation?",
        "What are the guidelines for alternative text on images?",
        "How should I make my forms accessible?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)
        results = vs.query(query, k=2)  # Get top 2 most relevant results
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"WCAG ID: {result.ref_id}")
            print(f"Title: {result.title}")
            print(f"Description: {result.description}")
            if result.url:
                print(f"URL: {result.url}")

if __name__ == "__main__":
    main()
