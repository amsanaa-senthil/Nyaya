from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION
import os
from dotenv import load_dotenv
load_dotenv()
import re

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
            api_key=api_key
        )
    if QDRANT_HOST.startswith("http"):
        return QdrantClient(url=QDRANT_HOST, api_key=api_key)
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

class VectorRetriever:
    def __init__(self):
        self.client = _create_client()
        self.collection_name = QDRANT_COLLECTION
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def search(self, query, top_k=5):
        query_vector = self.model.encode(query).tolist()

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )

        return [clean_text(point.payload.get("text", "")) for point in results.points]


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
    
    def search(self, query: str, top_k: int = 5) -> list[str]:
        """Search Qdrant vector database using Agno embedder"""
        query_vector = self.embedder.get_embedding(query)
        
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )
        
        return [clean_text(point.payload.get("text", "")) for point in results.points]


