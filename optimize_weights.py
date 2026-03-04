#!/usr/bin/env python3
"""
Phase 2: Optimize Retrieval Weights
Tests different semantic/BM25 balance ratios to find optimal configuration
"""

import json
import time
from agent.retriever import HybridRetriever

# Test configurations
# vector_weight is semantic (0-1), bm25_weight = 1 - vector_weight
WEIGHT_CONFIGS = [
    {"name": "Current (60/40)", "vector_weight": 0.6},
    {"name": "Semantic-Heavy (70/30)", "vector_weight": 0.7},
    {"name": "Semantic-Heavy (75/25)", "vector_weight": 0.75},
    {"name": "Balanced (65/35)", "vector_weight": 0.65},
    {"name": "BM25-Heavy (55/45)", "vector_weight": 0.55},
    {"name": "BM25-Heavy (50/50)", "vector_weight": 0.50},
]

def load_test_questions():
    """Load evaluation dataset for testing"""
    with open("evaluation_dataset.json", "r") as f:
        data = json.load(f)
    return data["evaluation_dataset"][:15]  # Test on first 15 questions

def run_optimization():
    """Test each weight configuration"""
    test_questions = load_test_questions()
    results = {}
    
    print("=" * 70)
    print("⚙️  PHASE 2: RETRIEVAL WEIGHT OPTIMIZATION")
    print("=" * 70)
    print(f"\nTesting on {len(test_questions)} sample questions\n")
    
    for config in WEIGHT_CONFIGS:
        vector_pct = int(config['vector_weight'] * 100)
        bm25_pct = 100 - vector_pct
        
        print(f"\n🔧 Testing: {config['name']}")
        print(f"   Weights: Semantic {vector_pct}% | BM25 {bm25_pct}%")
        print("-" * 70)
        
        retriever = HybridRetriever()
        
        latencies = []
        success_count = 0
        
        for i, test_case in enumerate(test_questions, 1):
            question = test_case["question"]
            try:
                start = time.time()
                # Test retrieval with specific weight
                chunks = retriever.search(
                    question, 
                    top_k=5, 
                    return_metadata=True,
                    vector_weight=config['vector_weight']
                )
                latency = time.time() - start
                latencies.append(latency)
                success_count += 1
            except Exception as e:
                print(f"  Q{i}: ❌ Error - {str(e)[:50]}")
                continue
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        results[config['name']] = {
            "success_rate": f"{success_count}/{len(test_questions)}",
            "avg_latency": f"{avg_latency:.2f}s",
            "vector_weight": config['vector_weight'],
            "bm25_weight": 1.0 - config['vector_weight']
        }
        
        print(f"  ✓ Success: {success_count}/{len(test_questions)} | Latency: {avg_latency:.2f}s")
    
    print("\n" + "=" * 70)
    print("📊 OPTIMIZATION RESULTS")
    print("=" * 70)
    
    for config_name, metrics in results.items():
        vector_pct = int(metrics['vector_weight'] * 100)
        bm25_pct = 100 - vector_pct
        print(f"\n{config_name}")
        print(f"  Success: {metrics['success_rate']}")
        print(f"  Avg Latency: {metrics['avg_latency']}")
    
    # Suggest best config
    fastest = min(results.items(), key=lambda x: float(x[1]['avg_latency'].rstrip('s')))
    print(f"\n🏆 FASTEST CONFIG: {fastest[0]}")
    print(f"   Latency: {fastest[1]['avg_latency']}")
    
    # Save results
    with open("optimization_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n✓ Results saved to optimization_results.json")

if __name__ == "__main__":
    run_optimization()
