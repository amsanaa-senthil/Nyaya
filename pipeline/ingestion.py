import os
from pipeline.extract_pdf import extract_text_from_pdf, extract_pages_from_pdf
from pipeline.chunk_pdf import chunk_text, chunk_pages_with_metadata
from pipeline.chunker import logical_chunking
from pipeline.embedder import embed_chunks
from pipeline.store_vectors import store_in_qdrant
from graph.neo4j_loader import create_case_node, create_citation_relationships
from graph.consolidate_graph import consolidate_duplicate_cases

PDF_FOLDER = "pdfs"

def process_all_pdfs():
    all_chunks = []
    all_embeddings = []

    for file in os.listdir(PDF_FOLDER):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(PDF_FOLDER, file)
            print(f"\nProcessing: {file}")

            pages = extract_pages_from_pdf(pdf_path)
            text = extract_text_from_pdf(pdf_path)

            chunks = chunk_pages_with_metadata(pages, file)
            citation_chunks = logical_chunking(text)

            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = embed_chunks(chunk_texts)

            store_in_qdrant(chunks, embeddings, file)

            # Pass text for metadata extraction
            create_case_node(file, text=text)

            create_citation_relationships(text, file, chunks=citation_chunks)

    print("\nAll PDFs processed successfully.")
    
    # Auto-deduplicate and merge OCR variants in Neo4j
    print("\n" + "="*60)
    print("Starting automatic deduplication of case nodes...")
    print("="*60)
    consolidate_duplicate_cases(similarity_threshold=0.85)
