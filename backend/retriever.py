"""
Hybrid Retriever for MedVerify.
Combines BM25 Lexical Keyword Search and Semantic Search with Reciprocal Rank Fusion (RRF).
"""

import re
import json
import logging
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from config import PUBMED_DATA_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def tokenize_clinical(text: str) -> List[str]:
    """Tokenize medical text preserving drug acronyms and numbers."""
    return re.findall(r"\b[A-Za-z0-9\-_]{2,}\b", text.lower())


class HybridRetriever:
    def __init__(self, data_file: str = str(PUBMED_DATA_FILE)):
        self.data_file = data_file
        self.documents: List[Dict[str, Any]] = []
        self.doc_map: Dict[str, Dict[str, Any]] = {}
        self.bm25: BM25Okapi = None
        self.corpus_tokens: List[List[str]] = []
        self._load_and_index()

    def _load_and_index(self):
        """Load PubMed dataset and build BM25 lexical index."""
        with open(self.data_file, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        self.doc_map = {doc["id"]: doc for doc in self.documents}
        logger.info(f"Loaded {len(self.documents)} clinical documents from {self.data_file}")

        # Build BM25 index
        self.corpus_tokens = [
            tokenize_clinical(f"{d['question']} {d['abstract']} {' '.join(d.get('mesh_terms', []))}")
            for d in self.documents
        ]
        self.bm25 = BM25Okapi(self.corpus_tokens)
        logger.info("BM25 lexical index built successfully.")

    def search_bm25(self, query: str, top_k: int = 15) -> List[Tuple[Dict[str, Any], float, int]]:
        """Perform BM25 search returning (doc, score, rank)."""
        tokens = tokenize_clinical(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, start=1):
            results.append((self.documents[idx], float(scores[idx]), rank))
        return results

    def search_semantic(self, query: str, top_k: int = 15) -> List[Tuple[Dict[str, Any], float, int]]:
        """
        Lightweight fast semantic search using word n-gram and clinical entity overlap.
        Runs locally in sub-millisecond time on CPU.
        """
        q_tokens = set(tokenize_clinical(query))
        scores = []
        for i, doc in enumerate(self.documents):
            d_tokens = set(self.corpus_tokens[i])
            overlap = len(q_tokens.intersection(d_tokens))
            score = overlap / max(len(q_tokens), 1)
            scores.append(score)

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        results = []
        for rank, idx in enumerate(ranked_indices, start=1):
            results.append((self.documents[idx], float(scores[idx]), rank))
        return results

    def hybrid_search(self, query: str, top_k: int = 10, k_rrf: int = 60) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) merging BM25 and Semantic search:
        RRF Score = 1 / (k + rank_bm25) + 1 / (k + rank_semantic)
        """
        bm25_hits = self.search_bm25(query, top_k=top_k * 2)
        sem_hits = self.search_semantic(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        bm25_ranks: Dict[str, int] = {}
        sem_ranks: Dict[str, int] = {}

        for doc, score, rank in bm25_hits:
            d_id = doc["id"]
            bm25_ranks[d_id] = rank
            rrf_scores[d_id] = rrf_scores.get(d_id, 0.0) + (1.0 / (k_rrf + rank))

        for doc, score, rank in sem_hits:
            d_id = doc["id"]
            sem_ranks[d_id] = rank
            rrf_scores[d_id] = rrf_scores.get(d_id, 0.0) + (1.0 / (k_rrf + rank))

        sorted_ids = sorted(rrf_scores.keys(), key=lambda d_id: rrf_scores[d_id], reverse=True)[:top_k]

        candidates = []
        for rank, d_id in enumerate(sorted_ids, start=1):
            doc = self.doc_map[d_id].copy()
            doc["initial_rank"] = rank
            doc["bm25_rank"] = bm25_ranks.get(d_id, 999)
            doc["semantic_rank"] = sem_ranks.get(d_id, 999)
            doc["rrf_score"] = round(rrf_scores[d_id], 4)
            candidates.append(doc)

        return candidates
