"""
RankGPT Cross-Reranker for MedVerify.
Re-scores candidate passages and prunes low-relevance distractor chunks using Gemini Flash.
"""

import logging
from typing import List, Dict, Any, Tuple
from gemini_client import GeminiClient
from config import RERANKED_TOP_K, RERANK_THRESHOLD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


RERANK_PROMPT = """You are an expert biomedical information retrieval evaluator.
Evaluate the clinical relevance of each candidate document to the given CLINICAL QUESTION.

Assign a relevance score from 0.0 (completely irrelevant) to 1.0 (directly answers the clinical trial question).

CLINICAL QUESTION: {query}

CANDIDATES:
{candidates_text}

Output JSON format:
{{
  "rankings": [
    {{"id": "doc_id", "relevance_score": 0.95, "reasoning": "Direct randomized trial on this exact drug and patient cohort."}},
    ...
  ]
}}
"""


class CrossReranker:
    def __init__(self, gemini_client: GeminiClient = None):
        self.gemini = gemini_client or GeminiClient()

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = RERANKED_TOP_K,
        threshold: float = RERANK_THRESHOLD
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Rerank retrieved candidates and prune low-scoring distractors.
        Returns (retained_docs, telemetry_info).
        """
        if not candidates:
            return [], {
                "total_input": 0,
                "retained_count": 0,
                "pruned_count": 0,
                "rank_shifts": []
            }

        candidates_str = ""
        for i, c in enumerate(candidates, start=1):
            candidates_str += f"\n[ID: {c['id']}] Title: {c['question']}\nAbstract Snippet: {c['abstract'][:300]}...\n"

        prompt = RERANK_PROMPT.format(query=query, candidates_text=candidates_str)
        res = self.gemini.generate_json(prompt, system_instruction="Output strictly valid JSON with relevance rankings.")
        rankings = res.get("data", {}).get("rankings", [])

        # Map scores to candidates
        score_map = {r.get("id"): float(r.get("relevance_score", 0.0)) for r in rankings if "id" in r}

        scored_docs = []
        for doc in candidates:
            item = doc.copy()
            # If RankGPT didn't return score, fallback to lexical overlap
            score = score_map.get(doc["id"])
            if score is None:
                q_words = set(query.lower().split())
                d_words = set(f"{doc['question']} {doc['abstract']}".lower().split())
                score = round(len(q_words.intersection(d_words)) / max(len(q_words), 1), 3)

            item["rerank_score"] = float(score)
            scored_docs.append(item)

        # Sort descending by rerank score
        sorted_docs = sorted(scored_docs, key=lambda x: x["rerank_score"], reverse=True)

        # Fix: filter by threshold FIRST, then take top_k — prevents discarding
        # high-scoring docs that happen to sit beyond the initial slice boundary.
        above_threshold = [d for d in sorted_docs if d["rerank_score"] >= threshold]
        below_threshold = [d for d in sorted_docs if d["rerank_score"] < threshold]

        # Safety fallback: if retrieval was requested and all docs fell below threshold, keep top-1 best candidate
        if not above_threshold and sorted_docs:
            logger.info(f"All candidates scored below {threshold}; retaining top-1 fallback ({sorted_docs[0]['id']}).")
            above_threshold = [sorted_docs[0]]
            below_threshold = sorted_docs[1:]

        # Log pruned docs
        for doc in below_threshold:
            logger.info(f"Pruned doc {doc['id']} (Score: {doc['rerank_score']:.2f} < Threshold {threshold})")

        # Take top_k from those that passed the threshold
        retained_docs_raw = above_threshold[:top_k]

        retained_docs = []
        rank_shifts = []

        for new_rank, doc in enumerate(retained_docs_raw, start=1):
            doc["reranked_rank"] = new_rank
            delta = doc["initial_rank"] - new_rank  # Positive = jumped UP
            doc["rank_delta"] = delta

            rank_shifts.append({
                "id": doc["id"],
                "pmid": doc["pmid"],
                "initial_rank": doc["initial_rank"],
                "reranked_rank": new_rank,
                "rank_delta": delta,
                "score": round(doc["rerank_score"], 3)
            })
            retained_docs.append(doc)

        # Accurate telemetry: count ALL docs that didn't make it into the final set
        pruned_count = len(below_threshold) + max(0, len(above_threshold) - top_k)
        telemetry = {
            "total_input": len(candidates),
            "retained_count": len(retained_docs),
            "pruned_count": pruned_count,
            "threshold": threshold,
            "rank_shifts": rank_shifts
        }

        return retained_docs, telemetry
