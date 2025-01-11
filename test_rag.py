from crew.wcag_rag import WCAGVectorStore

def test_rag_query():
    # Initialize vector store
    vs = WCAGVectorStore()
    
    # Test queries
    test_cases = [
        "Adding alt text to images in a web page",
        "Implementing keyboard navigation for a dropdown menu",
        "Setting color contrast for text and background",
        "Adding ARIA labels to custom buttons"
    ]
    
    for query in test_cases:
        print(f"\nQuery: {query}")
        print("-" * 50)
        
        results = vs.query_similar_guidelines(query)
        
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"Reference ID: {result['metadata']['ref_id']}")
            print(f"Title: {result['metadata']['title']}")
            print(f"URL: {result['metadata']['url']}")
            print(f"Score: {result['score']}")
            print("\nContent:")
            print(result['content'])
            print("-" * 50)

if __name__ == "__main__":
    test_rag_query()
