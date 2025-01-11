import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from typing import List, Dict, Optional
import json
import os
from pydantic import BaseModel
from .utils import get_llm

class WCAGGuideline(BaseModel):
    """Model for WCAG guideline"""
    ref_id: str
    title: str
    description: str
    url: str = ""
    techniques: List[str] = []
    failures: List[str] = []

    def to_text(self) -> str:
        # Add relevant keywords based on the guideline ID and title
        keywords = []
        categories = []
        
        # Perceivable (1.x)
        if self.ref_id.startswith("1.1"):
            keywords.extend(["alt text", "image descriptions", "non-text content", "screen readers"])
            categories.append("Text Alternatives")
        elif self.ref_id.startswith("1.2"):
            keywords.extend(["captions", "audio", "video", "multimedia", "transcripts"])
            categories.append("Time-based Media")
        elif self.ref_id.startswith("1.3"):
            keywords.extend(["structure", "semantics", "headings", "labels", "relationships"])
            categories.append("Adaptable Content")
        elif self.ref_id.startswith("1.4"):
            keywords.extend(["contrast", "color", "text size", "spacing", "visual presentation"])
            categories.append("Distinguishable Content")
            
        # Operable (2.x)
        elif self.ref_id.startswith("2.1"):
            keywords.extend(["keyboard", "navigation", "shortcuts", "input methods"])
            categories.append("Keyboard Accessibility")
        elif self.ref_id.startswith("2.2"):
            keywords.extend(["timing", "animations", "auto-updates", "interruptions"])
            categories.append("Time Limits")
        elif self.ref_id.startswith("2.3"):
            keywords.extend(["seizures", "flashing", "animations", "motion"])
            categories.append("Seizures and Physical Reactions")
        elif self.ref_id.startswith("2.4"):
            keywords.extend(["navigation", "landmarks", "headings", "focus", "links"])
            categories.append("Navigation")
        elif self.ref_id.startswith("2.5"):
            keywords.extend(["pointer", "touch", "gestures", "motion", "input methods"])
            categories.append("Input Modalities")
            
        # Understandable (3.x)
        elif self.ref_id.startswith("3.1"):
            keywords.extend(["language", "readability", "pronunciation"])
            categories.append("Readable Content")
        elif self.ref_id.startswith("3.2"):
            keywords.extend(["predictable", "consistency", "navigation", "behavior"])
            categories.append("Predictable Behavior")
        elif self.ref_id.startswith("3.3"):
            keywords.extend(["forms", "errors", "labels", "instructions", "validation"])
            categories.append("Input Assistance")
            
        # Robust (4.x)
        elif self.ref_id.startswith("4.1"):
            keywords.extend(["parsing", "compatibility", "aria", "status messages"])
            categories.append("Compatibility")
            
        keywords_str = ", ".join(keywords) if keywords else "No specific keywords"
        categories_str = ", ".join(categories) if categories else "Uncategorized"
        
        # Build techniques and failures sections
        techniques_str = "\nTechniques:\n" + "\n".join(f"- {t}" for t in self.techniques) if self.techniques else ""
        failures_str = "\nCommon Failures:\n" + "\n".join(f"- {f}" for f in self.failures) if self.failures else ""
        
        return f"""
        WCAG 2.2 Success Criterion {self.ref_id}: {self.title}
        
        Description:
        {self.description}
        
        Categories: {categories_str}
        Keywords: {keywords_str}{techniques_str}{failures_str}
        
        This guideline helps ensure web content is accessible to users with disabilities by addressing:
        - Users who rely on screen readers and assistive technologies
        - Users with visual impairments
        - Users with motor impairments
        - Users with cognitive disabilities
        
        Reference: {self.url or 'N/A'}
        """

class WCAGVectorStore:
    def __init__(self, persist_directory: str = ".chroma_db"):
        self.persist_directory = persist_directory
        # Use OpenAI embeddings with API key from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.collection_name = "wcag_2_2_guidelines_new"
        
    def initialize_db(self, wcag_file: str = "data/wcag_2_2_new.json"):
        """Initialize the vector store with WCAG 2.2 guidelines"""
        # Load WCAG 2.2 guidelines from JSON file
        with open(wcag_file, "r") as f:
            wcag_data = json.load(f)
        
        # Convert guidelines to WCAGGuideline objects
        guidelines = []
        for guideline in wcag_data["guidelines"]:
            # Extract ref_id and title from the name field (e.g., "1.1.1 Non-text Content")
            name_parts = guideline["name"].split(" ", 1)
            ref_id = name_parts[0]
            title = name_parts[1]
            
            wcag_guideline = WCAGGuideline(
                ref_id=ref_id,
                title=title,
                description=guideline["description"],
                url=guideline.get("url", f"https://www.w3.org/WAI/WCAG22/Understanding/{ref_id.lower()}.html"),
                techniques=guideline.get("techniques", []),
                failures=guideline.get("failures", [])
            )
            guidelines.append(wcag_guideline)
        
        # Create text splitter for chunking guidelines
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Convert guidelines to text and create chunks
        texts = []
        metadatas = []
        ids = []
        
        for i, guideline in enumerate(guidelines):
            guideline_text = guideline.to_text()
            chunks = text_splitter.create_documents([guideline_text])
            
            for j, chunk in enumerate(chunks):
                texts.append(chunk.page_content)
                metadatas.append({
                    "ref_id": guideline.ref_id,
                    "title": guideline.title,
                    "url": guideline.url,
                    "techniques": "|".join(guideline.techniques) if guideline.techniques else "",
                    "failures": "|".join(guideline.failures) if guideline.failures else ""
                })
                ids.append(f"guideline_{i}_chunk_{j}")
        
        # Create vector store
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        # Add texts to vector store
        self.vector_store.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        # Persist the vector store
        self.vector_store.persist()

    def query_similar_guidelines(self, code_description: str, k: int = 3) -> List[Dict]:
        """Query the vector store for similar WCAG guidelines based on code description"""
        # Create vector store if not already created
        if not hasattr(self, 'vector_store'):
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
        
        # Query vector store
        results = self.vector_store.similarity_search_with_score(code_description, k=k)
        
        # Process results
        guidelines = []
        seen_refs = set()  # Track seen ref_ids to avoid duplicates
        
        for doc, score in results:
            metadata = doc.metadata
            ref_id = metadata['ref_id']
            
            # Skip if we've already seen this guideline
            if ref_id in seen_refs:
                continue
            seen_refs.add(ref_id)
            
            # Create guideline object
            guideline = WCAGGuideline(
                ref_id=ref_id,
                title=metadata['title'],
                description=doc.page_content,
                url=metadata.get('url', ''),
                techniques=metadata.get('techniques', '').split("|") if metadata.get('techniques', '') else [],
                failures=metadata.get('failures', '').split("|") if metadata.get('failures', '') else []
            )
            
            guidelines.append({
                'guideline': guideline,
                'score': score,
                'text': guideline.to_text()
            })
        
        return guidelines

    def query(self, query_text: str, k: int = 3) -> List[WCAGGuideline]:
        """
        Query the vector store for relevant WCAG guidelines.
        
        Args:
            query_text (str): The query text to search for
            k (int): Number of results to return (default: 3)
            
        Returns:
            List[WCAGGuideline]: List of relevant WCAG guidelines
        """
        # Create Chroma client
        client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Try to get collection, initialize if it doesn't exist
        try:
            collection = client.get_collection(name=self.collection_name)
        except ValueError:
            self.initialize_db()
            collection = client.get_collection(name=self.collection_name)
        
        # Get embeddings for query
        query_embedding = self.embeddings.embed_query(query_text)
        
        # Query the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas"]
        )
        
        # Convert results to WCAGGuideline objects
        guidelines = []
        for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
            guideline = WCAGGuideline(
                ref_id=metadata['ref_id'],
                title=metadata['title'],
                description=doc,  # The document contains the description
                url=metadata.get('url', ''),
                techniques=metadata.get('techniques', '').split("|") if metadata.get('techniques', '') else [],
                failures=metadata.get('failures', '').split("|") if metadata.get('failures', '') else []
            )
            guidelines.append(guideline)
        
        return guidelines

def generate_code_description(diff_content: str, file_name: str) -> str:
    """Generate a semantic description of code changes for better RAG matching"""
    prompt = f"""
    Analyze this code diff and describe the accessibility-related changes or implications:
    
    File: {file_name}
    Diff:
    {diff_content}
    
    Focus on describing:
    1. UI elements being modified (buttons, forms, images, etc.)
    2. Semantic HTML changes
    3. ARIA attributes or roles
    4. Color or styling changes
    5. Interactive element behavior changes
    6. Content structure modifications
    7. Keyboard interaction changes
    8. Focus management
    9. Error handling and form validation
    10. Media alternatives
    
    Provide a concise but detailed description that captures the accessibility implications
    of these changes. Focus on how they might affect users with different disabilities.
    """
    
    llm = get_llm()
    return llm.predict(prompt)

def get_relevant_wcag_guidelines(diff_content: str, file_name: str) -> List[Dict]:
    """
    Main function to get relevant WCAG guidelines for a code diff.
    Returns a list of relevant guidelines with their content and matching scores.
    """
    # Initialize vector store if it doesn't exist
    vs = WCAGVectorStore()
    if not os.path.exists(vs.persist_directory):
        vs.initialize_db()
    
    # Generate semantic description of the code changes
    description = generate_code_description(diff_content, file_name)
    
    # Query similar guidelines
    return vs.query_similar_guidelines(description)
