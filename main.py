from pipeline.ingestion import process_all_pdfs
from graph.ranking_engine import show_most_cited_cases

if __name__ == "__main__":
    process_all_pdfs()

    print("\n--- Citation Ranking ---")
    show_most_cited_cases()
