# embedder.py
from sentence_transformers import SentenceTransformer

# Load model once globally
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_chunks(chunks):
    """
    Takes a list of text chunks and returns embeddings
    """
    embeddings = model.encode(chunks, show_progress_bar=True, convert_to_tensor=True)
    return embeddings
