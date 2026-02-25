import re
import os
import google.generativeai as genai
from agent.retriever import VectorRetriever, AgnoVectorRetriever, AGNO_AVAILABLE
from agent.graph_tool import CitationGraph
from agent.prompts import SYSTEM_PROMPT
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Optional imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import pipeline
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False

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
        
        # Initialize LLM stack with fallbacks
        self.gemini_available = False
        self.openai_available = False
        self.local_llm = None
        
        # Try initializing each LLM tier
        self._initialize_llm_stack()
    
    def _initialize_llm_stack(self):
        """Initialize all available LLM backends for fallback strategy"""
        # Tier 1: Gemini
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                self.gemini_available = True
                print("[1/3] Gemini API initialized")
            except Exception as e:
                print(f"[1/3] Gemini initialization failed: {e}")
        
        # Tier 2: OpenAI
        if OPENAI_API_KEY and OPENAI_AVAILABLE:
            try:
                openai.api_key = OPENAI_API_KEY
                self.openai_available = True
                print("[2/3] OpenAI API initialized")
            except Exception as e:
                print(f"[2/3] OpenAI initialization failed: {e}")
        
        # Tier 3: Local LLM (for offline fallback)
        if LOCAL_LLM_AVAILABLE:
            try:
                print("[3/3] Initializing local LLM (this may take a minute)...")
                self.local_llm = pipeline("text-generation", model="distilgpt2")
                print("[3/3] Local LLM initialized")
            except Exception as e:
                print(f"[3/3] Local LLM initialization failed: {e}")
        
        if not (self.gemini_available or self.openai_available or self.local_llm):
            raise ValueError("No LLM backend available. Please configure at least one of: GEMINI_API_KEY, OPENAI_API_KEY, or install transformers")

    def _generate_with_gemini(self, prompt):
        """Generate response using Gemini"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "429" in error_str or "resource exhausted" in error_str:
                print("[Gemini] Quota exceeded, falling back to OpenAI...")
                return None  # Signal to try next tier
            raise  # Re-raise other errors

    def _generate_with_openai(self, prompt):
        """Generate response using OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "rate limit" in error_str:
                print("[OpenAI] Rate limit exceeded, falling back to local LLM...")
                return None  # Signal to try next tier
            raise

    def _generate_with_local_llm(self, prompt):
        """Generate response using local LLM"""
        try:
            result = self.local_llm(prompt, max_length=200, num_return_sequences=1)
            return result[0]["generated_text"]
        except Exception as e:
            print(f"[Local LLM] Generation failed: {e}")
            raise

    def _generate_response(self, prompt):
        """
        Generate response with intelligent fallback strategy.
        Tries: Gemini -> OpenAI -> Local LLM
        """
        # Tier 1: Try Gemini
        if self.gemini_available:
            try:
                print("[LLM] Attempting Gemini...")
                response = self._generate_with_gemini(prompt)
                if response:
                    print("[LLM] Success with Gemini")
                    return response
            except Exception as e:
                print(f"[Gemini] Error: {e}")
        
        # Tier 2: Try OpenAI
        if self.openai_available:
            try:
                print("[LLM] Attempting OpenAI...")
                response = self._generate_with_openai(prompt)
                if response:
                    print("[LLM] Success with OpenAI")
                    return response
            except Exception as e:
                print(f"[OpenAI] Error: {e}")
        
        # Tier 3: Try Local LLM
        if self.local_llm:
            try:
                print("[LLM] Attempting local LLM...")
                response = self._generate_with_local_llm(prompt)
                print("[LLM] Success with local LLM")
                return response
            except Exception as e:
                print(f"[Local LLM] Error: {e}")
        
        # All fallbacks exhausted
        raise RuntimeError("All LLM backends failed. Unable to generate response.")

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
        
        # For general queries: retrieve context and use LLM with fallback
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
            return self._generate_response(prompt)
        except Exception as e:
            return f"Error: Unable to generate response across all LLM backends. {str(e)}"

