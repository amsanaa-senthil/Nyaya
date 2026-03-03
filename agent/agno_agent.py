import re
import time
from agent.retriever import HybridRetriever
from agent.graph_tool import CitationGraph
from optimizations import score_result_relevance, extract_query_terms
from agent.llm import generate_answer
from dotenv import load_dotenv

load_dotenv()

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
    def __init__(self, use_agno=False, show_debug=False):
        # Initialize graph and retriever
        self.graph = CitationGraph()
        self.show_debug = show_debug  # Suppress debug output for end users
        
        # Disable Agno for now (package incompatibility)
        self.use_agno = False
        
        if self.show_debug:
            print("[OK] Using hybrid retrieval (vector 60% + BM25 40%) with Neo4j integration")
        self.retriever = HybridRetriever()
        
        # Azure OpenAI is configured in llm.py
        self.last_llm_error = None

    def _generate_with_llm(self, prompt: str) -> str:
        """Generate answer using Azure OpenAI (configured in llm.py)"""
        try:
            self.last_llm_error = None
            answer = generate_answer(prompt)
            if answer and answer.strip():
                return answer
            raise RuntimeError("LLM returned an empty response")
        except Exception as error:
            self.last_llm_error = f"{type(error).__name__}: {error}"
            if self.show_debug:
                print(f"[DEBUG] LLM generation failed: {type(error).__name__}: {error}")
            raise

    def _build_retrieval_fallback_answer(self, query, clean_chunks):
        if not clean_chunks:
            return "Sorry, I couldn't find enough relevant information for that question in the current database."

        # Confidence gate: avoid hallucination/noisy dump
        first_cleaned, first_chunk = clean_chunks[0]
        first_dict = first_chunk if isinstance(first_chunk, dict) else {"text": first_cleaned}
        best_score = score_result_relevance(first_dict, query)

        query_terms = extract_query_terms(query)
        matched_query_terms = sum(1 for term in query_terms if term in first_cleaned.lower())

        if best_score < 0.10 or (len(query_terms) >= 3 and matched_query_terms == 0):
            return "Sorry, I couldn't find reliable information for that question in the current database."

        seen = set()
        unique = []
        for cleaned, chunk in clean_chunks:
            snippet_key = cleaned[:160].lower()
            if snippet_key in seen:
                continue
            seen.add(snippet_key)
            unique.append((cleaned, chunk))
            if len(unique) >= 2:
                break

        if not unique:
            return "Sorry, I couldn't find enough relevant information for that question in the current database."

        best_text, best_chunk = unique[0]
        best_excerpt = best_text[:350].strip()

        lines = ["Direct answer:", best_excerpt, "", "Sources:"]

        for i, (_, chunk) in enumerate(unique, 1):
            if not isinstance(chunk, dict):
                continue
            pdf = chunk.get("pdf_name") or "Unknown"
            page = chunk.get("page") if chunk.get("page") is not None else "?"
            lines.append(f"{i}. {pdf}, page {page}")

        lines.append("")
        error_text = (self.last_llm_error or "").lower()
        if any(marker in error_text for marker in ["resource_exhausted", "quota", "429", "api"]):
            lines.append("Note: This response is retrieval-only because the Azure OpenAI API is currently unavailable.")
        else:
            lines.append("Note: This response is retrieval-only because the LLM is currently unavailable.")
        return "\n".join(lines)

    def _build_case_source_block(self, case_name, top_k=2):
        lines = ["\n\n**Source Citations:**"]
        try:
            chunks = self.retriever.search(case_name, top_k=top_k, return_metadata=True)
        except Exception as e:
            lines.append(f"- Could not fetch supporting sources: {e}")
            return "\n".join(lines)

        added = 0
        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue

            text = clean_text(chunk.get("text", ""))
            if len(text) < 40:
                continue

            pdf = chunk.get("pdf_name") or "Unknown"
            page = chunk.get("page") if chunk.get("page") is not None else -1
            section = chunk.get("section") or "Unknown"
            quote = text[:260].strip().replace('"', "'")

            lines.append(f"{added + 1}. Case: {case_name}")
            lines.append(f"   PDF/File: {pdf}")
            lines.append(f"   Page: {page}")
            lines.append(f"   Section: {section}")
            lines.append(f"   Citation: \"{quote}\"")
            added += 1

            if added >= top_k:
                break

        if added == 0:
            lines.append("- No supporting quoted citation found in retrieved chunks.")

        return "\n".join(lines)

    def ask(self, query):
        query_lower = query.lower()

        # Guardrail: avoid wasting LLM calls on vague/low-information inputs
        query_terms = extract_query_terms(query)
        if len(query_terms) < 2 and len(query.split()) < 2:
            return "Please ask a more specific legal question (e.g., 'difference between civil and criminal burden of proof')."
        
        # ENHANCED: Detect specific case queries (e.g., "Bulankulama v. Secretary")
        # Pattern: "word v. word" or "word vs word" or "word vs. word"
        import re
        case_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:v\.|vs\.?|versus)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'
        case_match = re.search(case_pattern, query)
        
        if case_match:
            case_name = case_match.group(0)
            if self.show_debug:
                print(f"[ROUTER] Detected case query: {case_name}")
            
            # Get citation network from graph
            try:
                # Get cases this case cites
                cites = self.graph.get_cited_cases(case_name, limit=10)
                
                # Get cases that cite this case (DISTINCTION LEVEL)
                cited_by = self.graph.get_cited_by(case_name, limit=10)
                
                # Get citation count
                case_info = self.graph.get_case_info(case_name)
                
                if cited_by or cites or case_info:
                    result = f"**Citation Analysis: {case_name}**\n\n"
                    
                    if case_info:
                        citation_count = case_info.get("citation_count", 0)
                        result += f"This case has been cited {citation_count} times.\n\n"
                    
                    if cited_by:
                        result += f"**Cases that cite {case_name}:**\n"
                        for i, case in enumerate(cited_by, 1):
                            result += f"{i}. {case}\n"
                        result += "\n"
                    
                    if cites:
                        result += f"**Cases cited by {case_name}:**\n"
                        for i, case in enumerate(cites, 1):
                            result += f"{i}. {case}\n"

                    result += self._build_case_source_block(case_name)
                    return result
                else:
                    if self.show_debug:
                        print(f"[INFO] No citation data found for '{case_name}', checking similar case titles")
                    similar_cases = self.graph.find_similar_cases(case_name, limit=10)
                    if similar_cases:
                        result = f"**No exact citation network found for: {case_name}**\n\n"
                        result += "**Similar case titles in graph:**\n"
                        for i, case in enumerate(similar_cases, 1):
                            result += f"{i}. {case}\n"
                        result += "\nTry one of the above exact titles for network analysis."
                        result += self._build_case_source_block(case_name)
                        return result
                    if self.show_debug:
                        print(f"[INFO] No similar graph cases found for '{case_name}', falling back to retrieval")
            except Exception as e:
                if self.show_debug:
                    print(f"[WARNING] Graph query failed for case '{case_name}': {e}")
        
        # Handle citation-specific queries with graph data
        if "most cited" in query_lower or "top cited" in query_lower:
            try:
                start = time.time()
                top = self.graph.get_most_cited(50)  # Get more to filter duplicates
                if self.show_debug:
                    print("Graph query time:", time.time() - start)
            except Exception as e:
                if self.show_debug:
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
                if self.show_debug:
                    print("Graph query time:", time.time() - start)
            except Exception as e:
                if self.show_debug:
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
                    result += self._build_case_source_block(query)
                    return result
        
        # For general queries: retrieve context and use LLM
        try:
            start = time.time()
            context_chunks = self.retriever.search(query, top_k=3, return_metadata=True)
            if self.show_debug:
                print("Retrieval time:", time.time() - start)
        except Exception as e:
            if self.show_debug:
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
            return "I couldn't find relevant information in the database for your query. Please try rephrasing your question or ask about a different legal topic."
        
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
        self.last_llm_error = None
        
        # Build prompt for LLM - optimized for citation accuracy
        prompt = f"""You are Nyaya, an expert Sri Lankan legal assistant. Your role is to provide accurate legal answers grounded in provided case law and statutes.

Context from Sri Lankan case law:
{context_text}

Question: {query}

Instructions:
1. Answer the question clearly and accurately based on the provided documents
2. **CRITICAL: Cite specific cases or statute sections** whenever you make a legal statement
   - Example: "Under res judicata principle (as established in Silva v. Fernando), a final judgment prevents relitigation"
   - Example: "The burden of proof differs: civil cases require balance of probabilities, while criminal cases require beyond reasonable doubt"
3. If the context doesn't address the question, say "I don't have sufficient information in the provided documents to answer this"
4. Be concise but cite sources - a 2-sentence answer WITH citations is better than a long answer without citations
5. Do NOT make up case names or statute references that aren't in the provided documents

Remember: **Your credibility depends on accurate citations.** If you're uncertain, it's better to cite a specific source than to generalize."""
        
        try:
            answer = self._generate_with_llm(prompt)
            
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
            if self.show_debug:
                print(f"[DEBUG] LLM generation failed, using retrieval fallback: {e}")
            return self._build_retrieval_fallback_answer(query, clean_chunks)
