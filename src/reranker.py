"""
Neural Cross-Encoder Reranker for MedVerify.
Re-scores candidate passages and prunes low-relevance noise.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import RERANKER_MODEL, RERANKED_TOP_K, RERANK_SCORE_THRESHOLD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class NeuralReranker:
    def __init__(self, model_name: str = RERANKER_MODEL):
        self.model_name = model_name
        self.reranker = None
        self._init_reranker()

    def _init_reranker(self):
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading Cross-Encoder Reranker: {self.model_name}...")
            self.reranker = CrossEncoder(self.model_name)
            logger.info("Cross-Encoder Reranker loaded successfully.")
        except Exception as e:
            logger.warning(f"Cross-Encoder could not be loaded ({e}). Using lexical-density heuristic reranker.")
            self.reranker = None

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = RERANKED_TOP_K,
        threshold: float = RERANK_SCORE_THRESHOLD
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Rerank retrieved candidates using cross-attention.
        Returns (reranked_docs, telemetry_info).
        """
        if not candidates:
            return [], {"total_input": 0, "total_retained": 0, "rank_shifts": []}

        pairs = [[query, f"Title: {doc['question']}\nAbstract: {doc['content']}"] for doc in candidates]

        if self.reranker is not None:
            raw_scores = self.reranker.predict(pairs)
            # Normalize scores to 0-1 range using sigmoid if necessary
            import numpy as np
            scores = 1.0 / (1.0 + np.exp(-np.array(raw_scores)))
        else:
            # Fallback heuristic: word overlap ratio
            query_words = set(query.lower().split())
            scores = []
            for doc in candidates:
                doc_words = set(f"{doc['question']} {doc['content']}".lower().split())
                overlap = len(query_words.intersection(doc_words)) / max(len(query_words), 1)
                scores.append(min(1.0, overlap * 1.5))

        # Attach scores and initial ranks
        scored_candidates = []
        for i, doc in enumerate(candidates):
            item = doc.copy()
            item["raw_rerank_score"] = float(scores[i])
            item["initial_hybrid_rank"] = doc.get("hybrid_rank", i + 1)
            scored_candidates.append(item)

        # Sort by reranker score descending
        sorted_candidates = sorted(scored_candidates, key=lambda x: x["raw_rerank_score"], reverse=True)

        reranked_docs = []
        telemetry_shifts = []

        for new_rank, doc in enumerate(sorted_candidates[:top_k], start=1):
            if doc["raw_rerank_score"] < threshold:
                logger.info(f"Pruned doc {doc['id']} with score {doc['raw_rerank_score']:.3f} below threshold {threshold}")
                continue

            doc["reranked_rank"] = new_rank
            rank_delta = doc["initial_hybrid_rank"] - new_rank  # Positive means moved UP
            doc["rank_delta"] = rank_delta

            telemetry_shifts.append({
                "id": doc["id"],
                "pmid": doc["pmid"],
                "initial_rank": doc["initial_hybrid_rank"],
                "reranked_rank": new_rank,
                "rank_delta": rank_delta,
                "score": round(doc["raw_rerank_score"], 4)
            })
            reranked_docs.append(doc)

        telemetry = {
            "total_candidates_received": len(candidates),
            "candidates_retained": len(reranked_docs),
            "candidates_pruned": len(candidates) - len(reranked_docs),
            "threshold_applied": threshold,
            "rank_shifts": telemetry_shifts
        }

        return reranked_docs, telemetry
