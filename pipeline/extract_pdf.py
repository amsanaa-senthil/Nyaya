# extract_pdf.py

import fitz  # PyMuPDF
import re

def extract_text_from_pdf(pdf_path):
    """
    Extracts full text from a PDF file with preprocessing to clean OCR artifacts.
    """
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        full_text += page.get_text("text") + "\n"

    doc.close()
    
    # Preprocessing to improve text quality
    # Remove excessive spaces
    full_text = re.sub(r' +', ' ', full_text)
    # Fix broken line continuations (word-word\nword -> word-word word)
    full_text = re.sub(r'([a-z])-\s*\n\s*([a-z])', r'\1\2', full_text)
    # Join broken case names across lines
    full_text = re.sub(r'([A-Z][a-z]+)\s*\n\s*(v\.)', r'\1 \2', full_text)
    full_text = re.sub(r'(v\.)\s*\n\s*([A-Z][a-z]+)', r'\1 \2', full_text)
    # Normalize multiple dots
    full_text = re.sub(r'\.{2,}', '.', full_text)
    # Fix "v. ." to "v."
    full_text = re.sub(r'v\.\s*\.', 'v.', full_text)
    
    return full_text
