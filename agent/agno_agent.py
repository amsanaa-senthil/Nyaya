import re
import os
import time
from google import genai
from agent.retriever import VectorRetriever, AgnoVectorRetriever, AGNO_AVAILABLE
from agent.graph_tool import CitationGraph
from agent.prompts import SYSTEM_PROMPT
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

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
        self.model_name = GEMINI_MODEL

    def ask(self, query):
        query_lower = query.lower()
        
        # Handle citation-specific queries with graph data
        if "most cited" in query_lower or "top cited" in query_lower:
            try:
                start = time.time()
                top = self.graph.get_most_cited(50)  # Get more to filter duplicates
                print("Graph query time:", time.time() - start)
            except Exception as e:
                print("Graph query failed:", e)
                top = []
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
            try:
                start = time.time()
                cited = self.graph.get_cited_cases(query, 30)
                print("Graph query time:", time.time() - start)
            except Exception as e:
                print("Graph query failed:", e)
                cited = []
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
        try:
            start = time.time()
            context_chunks = self.retriever.search(query, top_k=3, return_metadata=True)
            print("Retrieval time:", time.time() - start)
        except Exception as e:
            print("Vector retrieval failed:", e)
            context_chunks = []
        
        # Clean and filter chunks
        clean_chunks = []
        for chunk in context_chunks:
            chunk_text = chunk.get("text", "") if isinstance(chunk, dict) else chunk
            cleaned = clean_text(chunk_text)
            # Skip very short chunks, but allow longer ones for legal content
            if len(cleaned) > 50:
                clean_chunks.append((cleaned, chunk))
        
        if not clean_chunks:
            return "I couldn't find relevant information in the database. Please try rephrasing your question."
        
        # Limit total context to avoid overwhelming the model
        context_blocks = []
        for cleaned, chunk in clean_chunks[:2]:
            if isinstance(chunk, dict):
                pdf = chunk.get("pdf_name") or "Unknown"
                page = chunk.get("page") or "Unknown"
                section = chunk.get("section") or "Unknown"
                line_start = chunk.get("line_start") or "Unknown"
                line_end = chunk.get("line_end") or "Unknown"
                context_blocks.append(
                    "TEXT:\n{0}\n\nSOURCE:\nPDF: {1}\nPage: {2}\nSection: {3}\nLines: {4}-{5}\n-----------------------".format(
                        cleaned, pdf, page, section, line_start, line_end
                    )
                )
            else:
                context_blocks.append(cleaned)

        context_text = "\n\n".join(context_blocks)
        
        # Simple, direct prompt
        prompt = f"""{SYSTEM_PROMPT}

Context from Sri Lankan case law:

{context_text}

Question: {query}

Answer the question based on the context above. Be concise and clear."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            answer = response.text
            
            # Append manual citations if not already present
            if isinstance(clean_chunks[0][1], dict) and "(Source:" not in answer:
                answer += "\n\n**Sources:**\n"
                for i, (_, chunk) in enumerate(clean_chunks[:2], 1):
                    if isinstance(chunk, dict):
                        pdf = chunk.get("pdf_name", "Unknown")
                        page = chunk.get("page", "?")
                        section = chunk.get("section", "Unknown")
                        line_start = chunk.get("line_start", "?")
                        line_end = chunk.get("line_end", "?")
                        answer += f"{i}. (Source: {pdf}, Page {page}, Section: {section}, Lines {line_start}-{line_end})\n"
            
            return answer
        except Exception as e:
            return f"LLM generation failed: {str(e)}"
