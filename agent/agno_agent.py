import re
import os
from google import genai
from agent.retriever import VectorRetriever, AgnoVectorRetriever, AGNO_AVAILABLE
from agent.graph_tool import CitationGraph
from agent.prompts import SYSTEM_PROMPT
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def clean_text(text):
    """
    Cleans OCR and PDF text:
    - removes extra spaces/newlines
    - removes soft hyphens
    """
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\xad', '')
    return text.strip()


class NyayaAgent:
    def __init__(self, use_agno=False):
        # Initialize graph and retriever
        self.graph = CitationGraph()
        
        # Disable Agno for now (package incompatibility)
        self.use_agno = False
        
        print("✓ Using standard retrieval with Neo4j integration")
        self.retriever = VectorRetriever()
        
        # Initialize Gemini client
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in .env file")
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def ask(self, query):
        query_lower = query.lower()
        
        # Handle citation-specific queries with graph data
        if "most cited" in query_lower or "top cited" in query_lower:
            top = self.graph.get_most_cited(50)  # Get more to filter duplicates
            if top:
                # Deduplicate and keep only unique cases (show top 20)
                seen = set()
                unique_cases = []
                for case, count in top:
                    # Normalize for deduplication
                    case_normalized = case.lower().strip()
                    if case_normalized not in seen:
                        seen.add(case_normalized)
                        unique_cases.append((case, count))
                    if len(unique_cases) >= 20:  # Limit to top 20 unique
                        break
                
                if unique_cases:
                    result = "**Top 20 Most Cited Cases:**\n\n"
                    for i, (case, count) in enumerate(unique_cases, 1):
                        result += f"{i}. {case.title()} - {count} citations\n"
                    return result
        
        # For specific case citation queries, return clean list
        if ("citations" in query_lower or "cited" in query_lower) and ("v." in query_lower or "vs" in query_lower):
            cited = self.graph.get_cited_cases(query, 30)
            if cited:
                # Deduplicate similar cases
                seen = set()
                unique_cited = []
                for case in cited:
                    case_normalized = case.lower().strip()
                    if case_normalized not in seen and len(case) > 5:
                        seen.add(case_normalized)
                        unique_cited.append(case)
                    if len(unique_cited) >= 15:
                        break
                
                if unique_cited:
                    result = f"**Cases cited in {query}:**\n\n"
                    for i, case in enumerate(unique_cited, 1):
                        result += f"{i}. {case.title()}\n"
                    return result
        
        # For general queries: retrieve context and use LLM
        context_chunks = self.retriever.search(query, top_k=3)  # Limit to 3 chunks
        
        # Clean and filter chunks
        clean_chunks = []
        for chunk in context_chunks:
            cleaned = clean_text(chunk)
            # Skip very short chunks, but allow longer ones for legal content
            if len(cleaned) > 50:
                clean_chunks.append(cleaned)
        
        if not clean_chunks:
            return "I couldn't find relevant information in the database. Please try rephrasing your question."
        
        # Limit total context to avoid overwhelming the model
        context_text = "\n\n".join(clean_chunks[:2])  # Max 2 chunks
        
        # Simple, direct prompt
        prompt = f"""{SYSTEM_PROMPT}

Context from Sri Lankan case law:

{context_text}

Question: {query}

Answer the question based on the context above. Be concise and clear."""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
