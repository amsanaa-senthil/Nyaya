import os
import json
from pipeline.extract_pdf import extract_text_from_pdf, extract_pages_from_pdf
from pipeline.chunk_pdf import chunk_pages_with_metadata
from pipeline.chunker import logical_chunking
from pipeline.embedder import embed_chunks
from pipeline.store_vectors import store_in_qdrant
from graph.neo4j_loader import create_case_node, create_citation_relationships
from graph.consolidate_graph import consolidate_duplicate_cases

PDF_FOLDER = "pdfs"
INDEX_STATE_FILE = ".index_state.json"


def _load_index_state():
    if not os.path.exists(INDEX_STATE_FILE):
        return {}
    try:
        with open(INDEX_STATE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_index_state(state):
    with open(INDEX_STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)


def _pdf_signature(pdf_path):
    stats = os.stat(pdf_path)
    return {
        "size": stats.st_size,
        "mtime_ns": stats.st_mtime_ns,
    }

def process_all_pdfs():
    index_state = _load_index_state()
    processed_count = 0
    skipped_count = 0

    for file in sorted(os.listdir(PDF_FOLDER)):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(PDF_FOLDER, file)
            current_signature = _pdf_signature(pdf_path)
            previous_signature = index_state.get(file)

            if previous_signature == current_signature:
                print(f"\nSkipping unchanged PDF: {file}")
                skipped_count += 1
                continue

            print(f"\nProcessing: {file}")

            pages = extract_pages_from_pdf(pdf_path)
            text = extract_text_from_pdf(pdf_path)

            chunks = chunk_pages_with_metadata(pages, file)
            citation_chunks = logical_chunking(text)

            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = embed_chunks(chunk_texts)

            store_in_qdrant(chunks, embeddings, file, replace_pdf=True)

            # Pass text for metadata extraction (Neo4j - optional)
            try:
                create_case_node(file, text=text)
                create_citation_relationships(text, file, chunks=citation_chunks)
            except Exception as e:
                print(f"[WARNING] Neo4j graph update failed for {file}: {e}")
                print("[INFO] Continuing with vector store indexing...")

            index_state[file] = current_signature
            _save_index_state(index_state)
            processed_count += 1

    print("\nAll PDFs processed successfully.")
    print(f"Processed: {processed_count} | Skipped unchanged: {skipped_count}")
    
    # Auto-deduplicate and merge OCR variants in Neo4j (optional)
    try:
        print("\n" + "="*60)
        print("Starting automatic deduplication of case nodes...")
        print("="*60)
        consolidate_duplicate_cases(similarity_threshold=0.85)
    except Exception as e:
        print(f"[WARNING] Neo4j deduplication failed: {e}")
        print("[INFO] Vector store is ready for queries.")
