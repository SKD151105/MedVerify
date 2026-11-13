"""
Evaluation metrics suite for MedVerify.
Computes Faithfulness, Hallucination Rate, Context Precision, and Token Efficiency.
"""

from typing import List, Dict, Any


def compute_faithfulness_rate(eval_results: List[Dict[str, Any]]) -> float:
    """Average faithfulness score across evaluated queries."""
    if not eval_results:
        return 0.0
    scores = [r.get("faithfulness", 0.0) for r in eval_results]
    return round(sum(scores) / len(scores), 3)


def compute_hallucination_rate(eval_results: List[Dict[str, Any]]) -> float:
    """Percentage of answers containing at least one contradicted or unsupported claim."""
    if not eval_results:
        return 0.0
    hallucinated_answers = sum(1 for r in eval_results if r.get("hallucinations_detected", 0) > 0)
    return round((hallucinated_answers / len(eval_results)) * 100, 1)


def compute_average_tokens(eval_results: List[Dict[str, Any]]) -> float:
    """Average tokens consumed per query."""
    if not eval_results:
        return 0.0
    tokens = [r.get("total_tokens", 0) for r in eval_results]
    return round(sum(tokens) / len(tokens), 1)


def compute_average_latency(eval_results: List[Dict[str, Any]]) -> float:
    """Average latency in seconds."""
    if not eval_results:
        return 0.0
    latencies = [r.get("latency_s", 0.0) for r in eval_results]
    return round(sum(latencies) / len(latencies), 2)
