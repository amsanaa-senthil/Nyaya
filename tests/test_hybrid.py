"""
Test script for hybrid retrieval (Phase 4)
"""
from agent.agno_agent import NyayaAgent
from dotenv import load_dotenv

load_dotenv()

# Initialize agent with hybrid retriever
print("\n" + "="*60)
print("PHASE 4: HYBRID RETRIEVAL TEST")
print("="*60 + "\n")

agent = NyayaAgent()

# Test queries with legal terminology
test_queries = [
    "Suez Canal Company case",
    "most cited cases in Indian constitution",
    "fundamental rights article 21",
]

for query in test_queries:
    print(f"\n[QUERY] '{query}'")
    print("-" * 60)
    
    try:
        response = agent.ask(query)
        print(f"Response:\n{response}\n")
    except Exception as e:
        print(f"⚠ Error: {e}\n")

print("\n" + "="*60)
print("Test completed!")
print("="*60)
