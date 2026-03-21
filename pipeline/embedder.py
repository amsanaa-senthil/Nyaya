# embedder.py
from sentence_transformers import SentenceTransformer

_model = None


def _get_model():
    global _model
    if _model is None:
        # Load model lazily so module import remains safe in CI test collection.
        _model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            local_files_only=True
        )
    return _model

def embed_chunks(chunks):
    """
    Takes a list of text chunks and returns embeddings
    """
    model = _get_model()
    embeddings = model.encode(chunks, show_progress_bar=True, convert_to_tensor=True)
    return embeddings
