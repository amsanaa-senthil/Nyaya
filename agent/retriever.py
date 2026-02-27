from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION
import os
from dotenv import load_dotenv
load_dotenv()
import re
from rank_bm25 import BM25Okapi
import numpy as np

try:
    from agno.knowledge.vector_db import VectorDB
    from agno.embedder.sentence_transformer import SentenceTransformerEmbedder
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    print("Warning: Agno not installed. Install with: pip install agno")

def clean_text(text):
    # Remove weird OCR hyphen splits
    text = re.sub(r'\xAD', '', text)
    text = re.sub(r'-\n', '', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n+', ' ', text)
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()



def _create_client():
    host = os.getenv("QDRANT_HOST")
    api_key = os.getenv("QDRANT_API_KEY")
    if host:
        return QdrantClient(
            url=host,
            api_key=api_key,
            timeout=60  # Increase timeout for cloud connections
        )
    if QDRANT_HOST.startswith("http"):
        return QdrantClient(url=QDRANT_HOST, api_key=api_key, timeout=60)
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

class VectorRetriever:
    def __init__(self):
        self.client = _create_client()
        self.collection_name = QDRANT_COLLECTION
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def search(self, query, top_k=5, return_metadata=True):
        query_vector = self.model.encode(query).tolist()

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )

        if not return_metadata:
            return [clean_text(point.payload.get("text", "")) for point in results.points]

        enriched = []
        for point in results.points:
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


class AgnoVectorRetriever:
    """Agno-powered retriever for Qdrant vector database"""
    def __init__(self):
        if not AGNO_AVAILABLE:
            raise ImportError("Agno not installed. Install with: pip install agno")
        
        self.client = _create_client()
        self.collection_name = QDRANT_COLLECTION
        self.embedder = SentenceTransformerEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    def search(self, query: str, top_k: int = 5, return_metadata=True) -> list[dict]:
        """Search Qdrant vector database using Agno embedder"""
        query_vector = self.embedder.get_embedding(query)
        
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )
        
        if not return_metadata:
            return [clean_text(point.payload.get("text", "")) for point in results.points]

        enriched = []
        for point in results.points:
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
                all_docs = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=10000  # Adjust if you have more documents
                )
            except Exception as scroll_err:
                print(f"[WARNING] Could not fetch all docs for BM25 (timeout or connection): {type(scroll_err).__name__}")
                print("[INFO] Switching to vector-only search (BM25 disabled)")
                self.documents = []
                self.bm25_model = None
                return
            
            # Extract text and tokenize for BM25
            for point in all_docs[0]:
                text = point.payload.get("text", "")
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
        
        # Get vector search results (always available)
        vector_results = self.vector_retriever.search(query, top_k=top_k*2, return_metadata=True)
        
        # Get BM25 scores (fallback to vector-only if BM25 failed)
        bm25_scores = {}
        if self.bm25_model and self.documents and len(self.documents) > 0:
            try:
                query_tokens = clean_text(query).lower().split()
                bm25_ranking = self.bm25_model.get_scores(query_tokens)
                
                # Create mapping of doc_id to BM25 score
                for i, score in enumerate(bm25_ranking):
                    bm25_scores[i] = score
            except Exception as e:
                print(f"[WARNING] BM25 scoring failed: {e}")
        
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
        )[:top_k]
        
        if return_metadata:
            return [result["doc"] for result in sorted_results]
        else:
            return [clean_text(result["doc"].get("text", "")) for result in sorted_results]


