#!/usr/bin/env python3
"""Test optimized prompt with sample query"""
from agent.agno_agent import NyayaAgent

agent = NyayaAgent(show_debug=True)

# Test a straightforward legal question
test_q = "What is the difference between civil and criminal burden of proof in Sri Lankan law?"

print("=" * 70)
print("Testing Optimized Prompt")
print("=" * 70)
print(f"\nQuery: {test_q}\n")
print("-" * 70)

try:
    answer = agent.ask(test_q)
    print(answer)
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
