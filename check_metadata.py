"""
Quick metadata audit script
Checks if all Qdrant chunks have complete page_number and pdf_name
"""
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

def audit_metadata():
    client = QdrantClient(
        url=os.getenv("QDRANT_HOST"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=60
    )
    
    collection_name = "sri_lankan_cases"
    
    print("="*60)
    print("QDRANT METADATA AUDIT")
    print("="*60)
    
    # Sample 100 random points
    results = client.scroll(
        collection_name=collection_name,
        limit=100
    )
    
    points = results[0]
    total = len(points)
    
    missing_page = 0
    missing_pdf = 0
    missing_section = 0
    complete = 0
    
    print(f"\nSampling {total} documents...\n")
    
    for point in points:
        payload = point.payload or {}
        
        has_page = payload.get("page") is not None
        has_pdf = bool(payload.get("pdf_name"))
        has_section = bool(payload.get("section"))
        
        if not has_page:
            missing_page += 1
        if not has_pdf:
            missing_pdf += 1
        if not has_section:
            missing_section += 1
        
        if has_page and has_pdf and has_section:
            complete += 1
    
    print(f"✓ Complete metadata: {complete}/{total} ({100*complete/total:.1f}%)")
    print(f"✗ Missing page:      {missing_page}/{total} ({100*missing_page/total:.1f}%)")
    print(f"✗ Missing pdf_name:  {missing_pdf}/{total} ({100*missing_pdf/total:.1f}%)")
    print(f"✗ Missing section:   {missing_section}/{total} ({100*missing_section/total:.1f}%)")
    
    if complete == total:
        print("\n✓ EXCELLENT: All chunks have complete metadata!")
    elif complete / total > 0.9:
        print("\n⚠ GOOD: >90% complete, but some chunks need fixing")
    else:
        print(f"\n✗ NEEDS WORK: Only {100*complete/total:.1f}% complete")
        print("   → Re-run: python main.py to re-index with fallback fixes")
    
    # Show a sample document
    if points:
        print("\n" + "="*60)
        print("SAMPLE DOCUMENT")
        print("="*60)
        sample = points[0].payload
        print(f"PDF: {sample.get('pdf_name', 'MISSING')}")
        print(f"Page: {sample.get('page', 'MISSING')}")
        print(f"Section: {sample.get('section', 'MISSING')}")
        print(f"Text preview: {sample.get('text', '')[:150]}...")

if __name__ == "__main__":
    audit_metadata()
