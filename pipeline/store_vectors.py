from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION
import os
import uuid
import time


def _create_client():
    """Create Qdrant client with longer timeout for cloud instances."""
    timeout_seconds = 300  # 5 minutes for cloud operations
    
    if QDRANT_HOST.startswith("http"):
        return QdrantClient(
            url=QDRANT_HOST, 
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=timeout_seconds
        )
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=timeout_seconds)

def store_in_qdrant(chunks, embeddings, pdf_name):
    client = _create_client()

    collection_name = QDRANT_COLLECTION

    # Create collection if it does not exist (avoid wiping previous data)
    try:
        client.get_collection(collection_name)
    except Exception:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=len(embeddings[0]),
                distance=Distance.COSINE
            )
        )

    points = []

    for chunk, embedding in zip(chunks, embeddings):
        # Convert tensor to list if needed
        vector = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "pdf": pdf_name,
                    "text": chunk
                }
            )
        )

    if points:
        # Batch upsert with retry logic to avoid timeouts on large datasets
        batch_size = 50  # Reduced from 100 for more reliable uploads
        max_retries = 3
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(points) + batch_size - 1) // batch_size
            
            # Retry logic with exponential backoff
            for attempt in range(max_retries):
                try:
                    print(f"  Batch {batch_num}/{total_batches}: uploading {len(batch)} points...", end="", flush=True)
                    client.upsert(collection_name=collection_name, points=batch)
                    print(" OK")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        print(f" TIMEOUT. Retrying in {wait_time}s (attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        print(f" FAILED after {max_retries} attempts")
                        raise
        
        print(f"[OK] Stored {len(points)} vectors for {pdf_name}")

    return client
