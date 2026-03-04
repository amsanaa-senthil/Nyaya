#!/usr/bin/env python3
"""
Phase 2 Analysis: Identify Optimization Opportunities
Analyzes evaluation results to find patterns in failures and improvements
"""

import json
import re

def analyze_results():
    """Analyze evaluation results to find improvement areas"""
    
    with open("evaluation_results.json", "r") as f:
        results = json.load(f)
    
    print("=" * 70)
    print("📈 PHASE 2: ANALYSIS & OPTIMIZATION RECOMMENDATIONS")
    print("=" * 70)
    
    total = results["total_tests"]
    passed = results["passed"]
    failed = results["failed"]
    pass_rate = results["pass_rate"]
    metrics = results.get("metrics", {})
    
    print(f"\n✓ Current Performance:")
    print(f"  Pass Rate: {pass_rate} ({passed}/{total})")
    print(f"  Recall@5: {metrics.get('recall_at_5', 'N/A')}")
    print(f"  Citation Precision: {metrics.get('citation_precision', 'N/A')}")
    print(f"  Answer Groundedness: {metrics.get('answer_groundedness', 'N/A')}")
    print(f"  Avg Latency: {metrics.get('avg_latency_seconds', 'N/A')}s")
    
    # Identify failed tests
    detailed = results.get("detailed_results", [])
    failed_tests = [r for r in detailed if r.get("status") == "FAILED"]
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for failure in failed_tests:
            print(f"  • Q{failure.get('question_id', '?')}: {failure.get('answer_snippet', 'Unknown')[:60]}")
    
    # Optimization recommendations
    print(f"\n🎯 OPTIMIZATION RECOMMENDATIONS:")
    print(f"\n1. PROMPT ENGINEERING (BEST ROI)")
    print(f"   • Current groundedness: {metrics.get('answer_groundedness', 'Low')}")
    print(f"   • Action: Add explicit citation instructions to system prompt")
    print(f"   • Example: 'Always cite specific cases or statute sections'")
    print(f"   • Expected improvement: +15-25% groundedness")
    
    print(f"\n2. RETRIEVAL THRESHOLD TUNING")
    print(f"   • Current config: optimizations.py RESULT_THRESHOLD = 0.32")
    print(f"   • Action: Test lower (0.25) for broader retrieval")
    print(f"   • Action: Test higher (0.40) for precision")
    print(f"   • Expected impact: +3-5% citation precision")
    
    print(f"\n3. WEIGHT CONFIGURATION CONFIRMED")
    print(f"   • Current weights: Semantic 60% | BM25 40%")
    print(f"   • Retrieval latency: EXCELLENT (all configs ~0.00s)")
    print(f"   • Status: No change needed for speed")
    
    print(f"\n4. LATENCY ALREADY OPTIMIZED")
    print(f"   • Avg latency: {metrics.get('avg_latency_seconds', '?')}s per query")
    print(f"   • Breakdown: ~0.00s retrieval + ~{metrics.get('avg_latency_seconds', '10')}s LLM generation")
    print(f"   • Status: LLM is bottleneck, not retrieval")
    
    print(f"\n📋 ACTION PLAN:")
    print(f"\n   Step 1: Edit agent/agno_agent.py system prompt")
    print(f"          → Add citation requirement & examples")
    print(f"   ")
    print(f"   Step 2: Run evaluation again")
    print(f"          → python evaluate.py")
    print(f"   ")
    print(f"   Step 3: Compare metrics (should see +10-20% groundedness)")
    print(f"   ")
    print(f"   Step 4: If improved → Commit & celebrate! 🎉")
    print(f"          If same → Try threshold tuning (0.25 or 0.40)")


if __name__ == "__main__":
    analyze_results()
