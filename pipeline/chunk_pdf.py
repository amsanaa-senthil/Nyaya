# chunk_pdf.py
import re

def chunk_text(text, chunk_size=300, overlap=50):
    """
    Logical semantic chunking for law reports:
    - Splits by paragraphs (handles both single and double newlines)
    - Merges paragraphs into chunks of ~chunk_size words
    - Adds optional overlap for context
    """
    # Normalize newlines
    text = re.sub(r'\n+', '\n', text).strip()
    
    # Try double newline split first, fallback to single newline
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) < 2:
        # No double newlines found, split by single newline
        paragraphs = [p.strip() for p in text.split("\n") if p.strip() and len(p.strip()) > 20]
    
    if not paragraphs:
        # Last resort: split into fixed-size word chunks
        words = text.split()
        paragraphs = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    
    chunks = []
    current_chunk = []

    for para in paragraphs:
        words_in_current = sum(len(p.split()) for p in current_chunk)
        words_in_para = len(para.split())

        if words_in_current + words_in_para <= chunk_size:
            current_chunk.append(para)
        else:
            # finalize current chunk
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            
            # start new chunk with overlap
            if overlap > 0 and current_chunk:
                # take last 'overlap' words from previous chunk
                overlap_words = []
                for p in reversed(current_chunk):
                    overlap_words = p.split() + overlap_words
                    if len(overlap_words) >= overlap:
                        break
                overlap_text = " ".join(overlap_words[-overlap:])
                current_chunk = [overlap_text, para]
            else:
                current_chunk = [para]

    # append remaining chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
