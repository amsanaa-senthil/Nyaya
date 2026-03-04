"""
Hybrid retrieval combining semantic search (Qdrant) and BM25 keyword search
Weights: Semantic 60% + BM25 40%
"""

from typing import List, Dict, Optional, Union
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from common_utils import clean_text, create_qdrant_client
from config import QDRANT_COLLECTION, EMBEDDING_MODEL
import numpy as np


class HybridRetriever:
    """Combines semantic (vector) and BM25 (keyword) retrieval"""
    
    def __init__(self, semantic_weight: float = 0.6, bm25_weight: float = 0.4):
        """
        Initialize hybrid retriever
        
        Args:
            semantic_weight: Weight for semantic/vector results (default 0.6)
            bm25_weight: Weight for BM25 keyword results (default 0.4)
        """
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
        
        # Initialize Qdrant client
        self.qdrant_client = create_qdrant_client()
        
        # Initialize embedding model
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Build BM25 index from collection
        self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Build BM25 index from all documents in Qdrant"""
        try:
            print("Building BM25 index from Qdrant collection...")
            
            # Scroll through all points in collection
            all_points = []
            all_texts = []
            
            # Get all points from collection
            scroll_result = self.qdrant_client.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=1000
            )
            
            points, _ = scroll_result
            all_points.extend(points)
            
            # Extract texts for BM25
            for point in all_points:
                payload = point.payload or {}
                text = payload.get("text", "")
                cleaned = clean_text(text)
                if cleaned:
                    all_texts.append(cleaned)
            
            # Tokenize and build BM25
            self.bm25_texts = all_texts
            tokenized_corpus = [doc.split() for doc in all_texts]
            self.bm25_index = BM25Okapi(tokenized_corpus)
            
            print(f"[OK] Built BM25 index from {len(all_texts)} documents")
        
        except Exception as e:
            print(f"[WARNING] BM25 index building failed: {e}")
            self.bm25_index = None
            self.bm25_texts = []
    
    def _semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search using vector embeddings (Qdrant)"""
        try:
            # Embed query
            query_embedding = self.embedding_model.encode(query)
            
            # Search in Qdrant using scroll-based approach
            search_results = []
            scroll_result = self.qdrant_client.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=10000
            )
            
            points, _ = scroll_result
            
            # Score and rank points
            scored_points = []
            for point in points:
                if point.payload is None:
                    continue
                    
                # Get point vector and compute similarity
                point_vector = point.vector if hasattr(point, 'vector') else None
                if point_vector is not None:
                    # Cosine similarity
                    sim = np.dot(query_embedding, point_vector) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(point_vector) + 1e-8
                    )
                    scored_points.append((sim, point))
            
            # Sort by score and get top-k
            scored_points.sort(key=lambda x: x[0], reverse=True)
            top_points = scored_points[:top_k]
            
            results = []
            for score, point in top_points:
                payload = point.payload or {}
                results.append({
                    "score": float(score),
                    "text": payload.get("text", ""),
                    "pdf_name": payload.get("pdf_name", "Unknown"),
                    "page": payload.get("page", "?"),
                    "section": payload.get("section", "Unknown"),
                    "line_start": payload.get("line_start", "?"),
                    "line_end": payload.get("line_end", "?"),
                })
            
            return results
        
        except Exception as e:
            print(f"[WARNING] Semantic search failed: {e}")
            return []
    
    def _bm25_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search using BM25 keyword matching"""
        try:
            if not self.bm25_index or not self.bm25_texts:
                return []
            
            # Tokenize query
            query_tokens = query.lower().split()
            
            # Get BM25 scores
            scores = self.bm25_index.get_scores(query_tokens)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include positive scores
                    text = self.bm25_texts[idx]
                    results.append({
                        "score": float(scores[idx]),
                        "text": text,
                        "pdf_name": "Unknown",  # BM25 index doesn't have metadata
                        "page": "?",
                        "section": "Unknown",
                        "line_start": "?",
                        "line_end": "?",
                    })
            
            return results
        
        except Exception as e:
            print(f"[WARNING] BM25 search failed: {e}")
            return []
    
    def _merge_results(
        self, 
        semantic_results: List[Dict], 
        bm25_results: List[Dict], 
        top_k: int = 5
    ) -> List[Dict]:
        """Merge and rank results from both retrievers"""
        
        # Normalize scores
        if semantic_results:
            max_semantic_score = max(r["score"] for r in semantic_results)
            for r in semantic_results:
                r["normalized_score"] = (r["score"] / max_semantic_score) if max_semantic_score > 0 else 0
        
        if bm25_results:
            max_bm25_score = max(r["score"] for r in bm25_results)
            for r in bm25_results:
                r["normalized_score"] = (r["score"] / max_bm25_score) if max_bm25_score > 0 else 0
        
        # Create combined ranking by text (to avoid duplicates)
        text_to_result = {}
        
        # Add semantic results
        for result in semantic_results:
            text_key = result["text"][:200]  # Use first 200 chars as key
            if text_key not in text_to_result:
                text_to_result[text_key] = {
                    **result,
                    "semantic_score": result.get("normalized_score", 0),
                    "bm25_score": 0,
                    "combined_score": 0,
                }
        
        # Add/merge BM25 results
        for result in bm25_results:
            text_key = result["text"][:200]
            if text_key not in text_to_result:
                text_to_result[text_key] = {
                    **result,
                    "semantic_score": 0,
                    "bm25_score": result.get("normalized_score", 0),
                    "combined_score": 0,
                }
            else:
                text_to_result[text_key]["bm25_score"] = result.get("normalized_score", 0)
        
        # Calculate combined scores
        for result in text_to_result.values():
            result["combined_score"] = (
                self.semantic_weight * result.get("semantic_score", 0) +
                self.bm25_weight * result.get("bm25_score", 0)
            )
        
        # Sort by combined score
        merged = sorted(
            text_to_result.values(),
            key=lambda r: r["combined_score"],
            reverse=True
        )[:top_k]
        
        return merged
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        return_metadata: bool = False
    ) -> Union[List[str], List[Dict]]:
        """
        Hybrid search combining semantic and BM25 retrieval
        
        Args:
            query: Search query
            top_k: Number of results to return
            return_metadata: If True, return full metadata dicts; if False, return text only
        
        Returns:
            List of results (strings if return_metadata=False, dicts if True)
        """
        # Get results from both retrievers
        semantic_results = self._semantic_search(query, top_k=top_k)
        bm25_results = self._bm25_search(query, top_k=top_k)
        
        # Merge and rank
        merged_results = self._merge_results(semantic_results, bm25_results, top_k=top_k)
        
        if return_metadata:
            return merged_results
        else:
            # Return text only
            return [r["text"] for r in merged_results]
