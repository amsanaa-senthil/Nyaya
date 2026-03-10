from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION
import os
from dotenv import load_dotenv
load_dotenv()
import re
from rank_bm25 import BM25Okapi
from optimizations import (
    get_cached_query_result,
    cache_query_result,
    filter_results_by_threshold,
    extract_query_terms,
    OPTIMIZED_SETTINGS,
)
from common_utils import clean_text, create_qdrant_client


def _enrich_points(points, return_metadata=True):
    """
    Helper: Convert Qdrant points to enriched result format.
    Eliminates code duplication between retrievers.
    """
    if not return_metadata:
        return [clean_text((point.payload or {}).get("text", "")) for point in points]
    
    enriched = []
    for point in points:
        payload = point.payload or {}
        enriched.append({
            "text": clean_text(payload.get("text", "")),
            "pdf_name": payload.get("pdf_name") or payload.get("pdf"),
            "page": payload.get("page"),
            "section": payload.get("section", "Unknown"),
            "line_start": payload.get("line_start"),
            "line_end": payload.get("line_end"),
        })
    return enriched


class VectorRetriever:
    def __init__(self):
        self.client = create_qdrant_client()
        self.collection_name = QDRANT_COLLECTION
        # Use local_files_only to avoid network permission issues on Windows
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            local_files_only=True
        )

    def search(self, query, top_k=5, return_metadata=True):
        query_vector = self.model.encode(query).tolist()

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )

        return _enrich_points(results.points, return_metadata)


class HybridRetriever:
    """
    Hybrid retriever combining vector search (semantic) and BM25 (keyword).
    
    Combines:
    - Vector search: 70% weight (semantic similarity)
    - BM25 search: 30% weight (exact matches, legal terms)
    
    This improves precision for legal queries which often include:
    - Exact case names
    - Specific legal citations
    - Domain-specific terminology
    """
    
    def __init__(self):
        self.vector_retriever = VectorRetriever()
        self.client = self.vector_retriever.client
        self.collection_name = self.vector_retriever.collection_name
        self.bm25_corpus = None
        self.bm25_model = None
        self.documents = None
        
        # Build BM25 index from all documents in Qdrant
        self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Fetch all documents from Qdrant and build BM25 index"""
        try:
            # Initialize as empty list (not None) to avoid NoneType errors
            self.documents = []
            documents = []
            
            # Get all documents from Qdrant
            # For cloud instances, fetching all documents can timeout
            # In that case, we fallback to vector-only search
            try:
                import socket
                all_docs = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=10000,  # Adjust if you have more documents
                    timeout=30  # 30 second timeout to prevent hanging
                )
            except (TimeoutError, socket.error, OSError, ConnectionError) as scroll_err:
                print(f"[WARNING] Could not fetch all docs for BM25 (network/timeout): {type(scroll_err).__name__}")
                print("[INFO] Switching to vector-only search (BM25 disabled)")
                self.documents = []
                self.bm25_model = None
                return
            except Exception as scroll_err:
                print(f"[WARNING] Could not fetch all docs for BM25: {type(scroll_err).__name__}")
                print("[INFO] Switching to vector-only search (BM25 disabled)")
                self.documents = []
                self.bm25_model = None
                return
            
            # Extract text and tokenize for BM25
            for point in all_docs[0]:
                text = (point.payload or {}).get("text", "")
                cleaned = clean_text(text)
                if len(cleaned) > 20:  # Skip very short docs
                    # Tokenize: split by whitespace and lowercase
                    tokens = cleaned.lower().split()
                    documents.append(tokens)
                    self.documents.append({
                        "text": cleaned,
                        "id": point.id,
                        "payload": point.payload or {}
                    })
            
            # Build BM25 model
            if documents:
                self.bm25_model = BM25Okapi(documents)
                print(f"[OK] Built BM25 index from {len(documents)} documents")
            else:
                print("[WARNING] No documents found for BM25 indexing")
                self.documents = []
                
        except Exception as e:
            print(f"[WARNING] Failed to build BM25 index: {e}")
            # Ensure documents is an empty list, not None
            if self.documents is None:
                self.documents = []
            self.bm25_model = None
    
    def search(self, query, top_k=5, return_metadata=True, vector_weight=0.6):
        """
        Hybrid search combining vector and BM25 scores.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            return_metadata: Include document metadata
            vector_weight: Weight for vector score (0.0-1.0), BM25 gets (1-vector_weight)
            
        Returns:
            List of ranked documents
        """
        bm25_weight = 1.0 - vector_weight
        
        # Check cache first (skip if exact match found)
        if OPTIMIZED_SETTINGS.get("cache_enabled"):
            cached = get_cached_query_result(query)
            if cached:
                # Debug: print(f"[CACHE HIT] Retrieved cached results for query")
                if return_metadata:
                    return cached[:top_k]
                return [r.get("text", "") for r in cached[:top_k]]
        
        # Get vector search results (always available)
        vector_results = self.vector_retriever.search(query, top_k=top_k*2, return_metadata=True)
        
        # Get BM25 scores (fallback to vector-only if BM25 failed)
        bm25_scores = {}
        if self.bm25_model and self.documents and len(self.documents) > 0:
            try:
                query_tokens = extract_query_terms(query)
                if not query_tokens:
                    query_tokens = clean_text(query).lower().split()
                bm25_ranking = self.bm25_model.get_scores(query_tokens)
                
                # Create mapping of doc_id to BM25 score
                for i, score in enumerate(bm25_ranking):
                    bm25_scores[i] = score
            except Exception as e:
                pass
        
        # Combine and rank results
        combined_results = {}
        
        # Add vector results with vector scores
        for i, doc in enumerate(vector_results):
            doc_id = id(doc)  # Use doc object id as key
            # Vector score is already normalized (0-1) by Qdrant
            vector_score = 1.0 - (i / (len(vector_results) + 1))  # Inverse rank scoring
            combined_results[doc_id] = {
                "doc": doc,
                "vector_score": vector_score,
                "bm25_score": 0.0,
                "final_score": vector_score * vector_weight
            }
        
        # Add BM25 scores for documents (only if available)
        if self.documents and len(self.documents) > 0:
            for i, doc in enumerate(self.documents):
                bm25_score = bm25_scores.get(i, 0.0)
                if bm25_score > 0:
                    doc_id = id(doc)
                    # Normalize BM25 score to 0-1 range
                    max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
                    normalized_bm25 = bm25_score / max(max_bm25, 1.0)
                    
                    if doc_id in combined_results:
                        # Update existing result
                        combined_results[doc_id]["bm25_score"] = normalized_bm25
                        combined_results[doc_id]["final_score"] = (
                            combined_results[doc_id]["vector_score"] * vector_weight +
                            normalized_bm25 * bm25_weight
                        )
                    else:
                        # Add new result from BM25
                        combined_results[doc_id] = {
                            "doc": {
                                "text": doc["text"],
                                "pdf_name": doc["payload"].get("pdf_name", "Unknown"),
                                "page": doc["payload"].get("page", "Unknown"),
                                "section": doc["payload"].get("section", "Unknown"),
                                "line_start": doc["payload"].get("line_start"),
                                "line_end": doc["payload"].get("line_end"),
                            },
                            "vector_score": 0.0,
                            "bm25_score": normalized_bm25,
                            "final_score": normalized_bm25 * bm25_weight
                        }
        
        # Sort by final score and return top_k
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x["final_score"],
            reverse=True
        )
        
        # Apply relevance filtering (accuracy improvement)
        docs_for_filtering = [r["doc"] for r in sorted_results]
        filtered_results = filter_results_by_threshold(
            docs_for_filtering,
            query,
            threshold=OPTIMIZED_SETTINGS.get("result_threshold", 0.32)
        )[:top_k]
        
        # Cache results for future queries
        if OPTIMIZED_SETTINGS.get("cache_enabled"):
            cache_query_result(query, filtered_results)
        
        if return_metadata:
            return filtered_results
        else:
            return [clean_text(r.get("text", "")) for r in filtered_results]


