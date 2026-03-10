"""
Test hybrid retrieval without calling LLM (avoids API quota issues)
"""
from agent.retriever import HybridRetriever

print("Initializing hybrid retriever...")
retriever = HybridRetriever()

# Test queries
queries = [
    "Suez Canal Company case",
    "fundamental rights article 21",
    "Section 302 IPC"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: '{query}'")
    print('='*60)
    
    results = retriever.search(query, top_k=3, return_metadata=True)
    
    for i, doc in enumerate(results, 1):
        print(f"\n[Result {i}]")
        if isinstance(doc, dict):
            print(f"PDF: {doc.get('pdf_name', 'Unknown')}")
            print(f"Page: {doc.get('page', '?')}")
            print(f"Section: {doc.get('section', 'Unknown')}")
            print(f"Text preview: {doc.get('text', '')[:200]}...")
        else:
            print(f"Text: {doc[:200]}...")

print(f"\n{'='*60}")
print("Retrieval test complete!")
