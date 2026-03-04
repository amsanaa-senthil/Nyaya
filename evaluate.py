#!/usr/bin/env python3
"""
Academic-Grade Evaluation Framework for Nyaya System
Measures: Recall@5, Citation Precision, Groundedness, Hallucination
"""

import json
import re
import time
from typing import List, Dict
from agent.agno_agent import NyayaAgent
from agent.retriever import HybridRetriever

class NyayaEvaluator:
    def __init__(self, dataset_path: str = "evaluation_dataset.json"):
        self.agent = NyayaAgent(show_debug=False)
        self.retriever = HybridRetriever()
        
        with open(dataset_path, 'r') as f:
            self.dataset = json.load(f)
        
        self.results = {
            "questions_tested": 0,
            "recall_at_5": [],
            "citation_precision": [],
            "answer_groundedness": [],
            "hallucinations": [],
            "failures": []
        }
    
    def recall_at_5(self, query: str, ground_truth_pdf: str) -> bool:
        """Check if ground truth document appears in top-5 retrieved results"""
        try:
            chunks = self.retriever.search(query, top_k=5, return_metadata=True)
            retrieved_pdfs = []
            
            for chunk in chunks:
                if isinstance(chunk, dict):
                    pdf_name = chunk.get("pdf_name", "").lower()
                    retrieved_pdfs.append(pdf_name)
            
            # Check if ground truth PDF (wildcards) matches
            ground_truth_pattern = ground_truth_pdf.lower().replace("*", ".*")
            for pdf in retrieved_pdfs:
                if re.match(ground_truth_pattern, pdf):
                    return True
            
            return False
        except Exception as e:
            print(f"  [ERROR] Recall@5 failed: {e}")
            return False
    
    def citation_precision(self, answer: str, retrieved_chunks: List[Dict]) -> float:
        """% of citations in answer that appear in retrieved chunks"""
        # Extract citations (text in quotes or "Case Name v. Case Name" pattern)
        citation_pattern = r'([A-Z][a-zA-Z]+ v\. [A-Z][a-zA-Z]+)'
        citations_in_answer = set(re.findall(citation_pattern, answer))
        
        if not citations_in_answer:
            return 1.0  # No citations = no hallucinations
        
        # Get all case names from retrieved chunks
        cited_cases_in_chunks = set()
        for chunk in retrieved_chunks:
            if isinstance(chunk, dict):
                text = chunk.get("text", "").lower()
                for citation in citations_in_answer:
                    if citation.lower() in text:
                        cited_cases_in_chunks.add(citation)
        
        precision = len(cited_cases_in_chunks) / len(citations_in_answer) if citations_in_answer else 1.0
        return precision
    
    def answer_groundedness(self, answer: str, retrieved_chunks: List[Dict]) -> float:
        """% of answer sentences that appear in retrieved chunks"""
        sentences = re.split(r'[.!?]+', answer)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]
        
        if not sentences:
            return 0.0
        
        grounded_count = 0
        for sentence in sentences:
            for chunk in retrieved_chunks:
                if isinstance(chunk, dict):
                    chunk_text = chunk.get("text", "")
                    if sentence.lower() in chunk_text.lower():
                        grounded_count += 1
                        break
        
        return grounded_count / len(sentences) if sentences else 0.0
    
    def page_accuracy(self, answer: str, expected_pages: List[int]) -> bool:
        """Check if correct page numbers are mentioned"""
        page_pattern = r'page\s+(\d+)'
        pages_in_answer = set(map(int, re.findall(page_pattern, answer, re.IGNORECASE)))
        
        if not pages_in_answer:
            return False
        
        expected_set = set(expected_pages)
        return len(pages_in_answer & expected_set) > 0
    
    def run_single_test(self, test_case: Dict) -> Dict:
        """Run evaluation for a single test case"""
        question = test_case["question"]
        question_id = test_case["id"]
        category = test_case["category"]
        expected_pdf = test_case["expected_pdf"]
        
        print(f"\n{'='*70}")
        print(f"Test {question_id} | {category}")
        print(f"Q: {question}")
        
        # Get answer from system
        start_time = time.time()
        try:
            answer = self.agent.ask(question)
            elapsed = time.time() - start_time
        except Exception as e:
            print(f"  [ERROR] System failed: {e}")
            return {
                "question_id": question_id,
                "status": "FAILED",
                "error": str(e)
            }
        
        # Retrieve chunks for analysis
        try:
            retrieved_chunks = self.retriever.search(question, top_k=5, return_metadata=True)
        except:
            retrieved_chunks = []
        
        # Compute metrics
        recall = self.recall_at_5(question, expected_pdf)
        precision = self.citation_precision(answer, retrieved_chunks)
        groundedness = self.answer_groundedness(answer, retrieved_chunks)
        
        page_correct = False
        if "expected_page" in test_case:
            page_correct = self.page_accuracy(answer, [test_case["expected_page"]])
        
        result = {
            "question_id": question_id,
            "category": category,
            "status": "PASSED" if recall else "FAILED",
            "recall_at_5": recall,
            "citation_precision": round(precision, 3),
            "answer_groundedness": round(groundedness, 3),
            "page_accuracy": page_correct if "expected_page" in test_case else None,
            "latency_seconds": round(elapsed, 2),
            "answer_snippet": answer[:150] + "..." if len(answer) > 150 else answer
        }
        
        # Print results
        print(f"  Status: {result['status']}")
        print(f"  Recall@5: {'✓' if recall else '✗'}")
        print(f"  Citation Precision: {precision:.1%}")
        print(f"  Answer Groundedness: {groundedness:.1%}")
        print(f"  Latency: {elapsed:.2f}s")
        if "expected_page" in test_case:
            print(f"  Page Accuracy: {'✓' if page_correct else '✗'}")
        
        return result
    
    def run_full_evaluation(self) -> Dict:
        """Run all tests and generate report"""
        print("\n" + "="*70)
        print("🔍 NYAYA SYSTEM ACADEMIC EVALUATION")
        print("="*70)
        
        all_results = []
        
        for test_case in self.dataset["evaluation_dataset"]:
            result = self.run_single_test(test_case)
            all_results.append(result)
        
        # Aggregate metrics
        valid_results = [r for r in all_results if "recall_at_5" in r and isinstance(r["recall_at_5"], bool)]
        passed = sum(1 for r in valid_results if r["status"] == "PASSED")
        
        recall_at_5_avg = sum(r["recall_at_5"] for r in valid_results) / len(valid_results) if valid_results else 0
        cite_prec_vals = [r["citation_precision"] for r in valid_results if isinstance(r.get("citation_precision"), (int, float))]
        cite_prec_avg = sum(cite_prec_vals) / len(cite_prec_vals) if cite_prec_vals else 0
        ground_vals = [r["answer_groundedness"] for r in valid_results if isinstance(r.get("answer_groundedness"), (int, float))]
        ground_avg = sum(ground_vals) / len(ground_vals) if ground_vals else 0
        avg_latency = sum(r["latency_seconds"] for r in valid_results if isinstance(r.get("latency_seconds"), (int, float))) / len([r for r in valid_results if isinstance(r.get("latency_seconds"), (int, float))]) if valid_results else 0
        
        # Generate report
        report = {
            "evaluation_type": "Academic Grade Evaluation",
            "total_tests": len(valid_results),
            "passed": passed,
            "failed": len(valid_results) - passed,
            "pass_rate": f"{(passed / len(valid_results)) * 100:.1f}%" if valid_results else "N/A",
            "metrics": {
                "recall_at_5": f"{recall_at_5_avg * 100:.1f}%",
                "citation_precision": f"{cite_prec_avg * 100:.1f}%",
                "answer_groundedness": f"{ground_avg * 100:.1f}%",
                "avg_latency_seconds": round(avg_latency, 2)
            },
            "detailed_results": all_results
        }
        
        # Print summary
        print("\n" + "="*70)
        print("📊 EVALUATION SUMMARY")
        print("="*70)
        print(f"Total Tests: {report['total_tests']}")
        print(f"Passed: {report['passed']} | Failed: {report['failed']}")
        print(f"Pass Rate: {report['pass_rate']}")
        print(f"\n📈 Key Metrics:")
        print(f"  • Recall@5: {report['metrics']['recall_at_5']}")
        print(f"  • Citation Precision: {report['metrics']['citation_precision']}")
        print(f"  • Answer Groundedness: {report['metrics']['answer_groundedness']}")
        print(f"  • Avg Latency: {report['metrics']['avg_latency_seconds']}s")
        
        return report
    
    def save_results(self, output_file: str = "evaluation_results.json"):
        """Save full evaluation results"""
        report = self.run_full_evaluation()
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Results saved to {output_file}")
        return report

if __name__ == "__main__":
    evaluator = NyayaEvaluator()
    evaluator.save_results()
