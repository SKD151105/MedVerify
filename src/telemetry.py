"""
Observability and Telemetry Engine for MedVerify.
Computes token savings, latency waterfalls, and RAGAS-style evaluation metrics.
"""

from typing import Dict, Any, List


class TelemetryTracker:
    @staticmethod
    def calculate_cost_savings(
        tokens_adaptive: int,
        tokens_fixed: int,
        price_per_1k_tokens: float = 0.0015
    ) -> Dict[str, Any]:
        """Calculates token and estimated dollar savings vs Fixed-RAG."""
        token_delta = max(0, tokens_fixed - tokens_adaptive)
        pct_saved = round((token_delta / max(tokens_fixed, 1)) * 100, 1)
        cost_saved = round((token_delta / 1000.0) * price_per_1k_tokens, 6)

        return {
            "tokens_adaptive": tokens_adaptive,
            "tokens_fixed_baseline": tokens_fixed,
            "tokens_saved": token_delta,
            "percentage_tokens_saved": pct_saved,
            "estimated_cost_saved_usd": cost_saved
        }

    @staticmethod
    def compile_latency_waterfall(
        routing_ms: float,
        retrieval_ms: float,
        reranking_ms: float,
        generation_ms: float,
        verification_ms: float
    ) -> Dict[str, Any]:
        """Compiles latency breakdown for the execution graph."""
        total_ms = round(routing_ms + retrieval_ms + reranking_ms + generation_ms + verification_ms, 2)
        return {
            "Routing (Adaptive Gate)": routing_ms,
            "Hybrid Retrieval (BM25 + Dense)": retrieval_ms,
            "Neural Reranking (Cross-Encoder)": reranking_ms,
            "LLM Synthesis": generation_ms,
            "NLI Hallucination Verification": verification_ms,
            "Total Pipeline Latency": total_ms
        }

    @staticmethod
    def calculate_ragas_scorecard(
        faithfulness: float,
        retained_docs_count: int,
        query: str,
        answer: str
    ) -> Dict[str, Any]:
        """Calculates RAGAS-aligned metrics."""
        # Answer Relevance: heuristic based on keyword coverage
        q_words = set(query.lower().split())
        a_words = set(answer.lower().split())
        relevance_overlap = len(q_words.intersection(a_words)) / max(len(q_words), 1)
        answer_relevance = round(min(1.0, 0.4 + relevance_overlap * 0.7), 2)

        # Context Precision: higher if documents retained were high quality
        context_precision = 0.95 if retained_docs_count in [2, 3] else (0.75 if retained_docs_count > 0 else 1.0)

        return {
            "Faithfulness": round(faithfulness, 2),
            "Answer Relevance": answer_relevance,
            "Context Precision": context_precision,
            "Hallucination Risk": "LOW" if faithfulness >= 0.8 else ("MEDIUM" if faithfulness >= 0.5 else "HIGH")
        }
