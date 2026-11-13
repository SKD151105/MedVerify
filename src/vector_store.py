"""
Hybrid Vector Store & Retrieval Engine for MedVerify.
Combines BM25 (lexical) and Dense Vector Embeddings with Reciprocal Rank Fusion (RRF).
"""

import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

from config import DENSE_EMBEDDING_MODEL, CHROMA_PERSIST_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def simple_tokenize(text: str) -> List[str]:
    """Basic medical text tokenizer for BM25."""
    return re.findall(r"\b[A-Za-z0-9\-_]{2,}\b", text.lower())


class HybridRetriever:
    def __init__(self, documents: List[Dict[str, Any]]):
        self.documents = documents
        self.doc_map = {doc["id"]: doc for doc in documents}
        
        # Initialize BM25 Index
        logger.info(f"Building BM25 index over {len(documents)} clinical documents...")
        self.tokenized_corpus = [
            simple_tokenize(f"{doc['question']} {doc['content']} {' '.join(doc.get('mesh_terms', []))}")
            for doc in documents
        ]
        if BM25Okapi is not None:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.bm25 = None

        # Initialize Dense Embedder
        self.dense_model = None
        self.doc_embeddings = None
        self._init_dense_embedder()

    def _init_dense_embedder(self):
        """Try loading sentence-transformers for dense embeddings, with graceful fallback."""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            logger.info(f"Loading dense embedding model: {DENSE_EMBEDDING_MODEL}...")
            self.dense_model = SentenceTransformer(DENSE_EMBEDDING_MODEL)
            texts = [f"Title: {doc['question']}\nAbstract: {doc['content']}" for doc in self.documents]
            self.doc_embeddings = self.dense_model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            logger.info("Dense embedding index successfully built.")
        except Exception as e:
            logger.warning(f"Dense embedder could not be initialized ({e}). Operating in BM25-prioritized mode.")
            self.dense_model = None

    def search_bm25(self, query: str, top_k: int = 15) -> List[Tuple[Dict[str, Any], float, int]]:
        """Perform BM25 search returning (doc, score, rank)."""
        tokens = simple_tokenize(query)
        if not tokens:
            return []

        if self.bm25 is not None:
            scores = self.bm25.get_scores(tokens)
        else:
            # Fallback term-frequency overlap
            q_set = set(tokens)
            scores = []
            for doc_toks in self.tokenized_corpus:
                overlap = sum(1 for t in doc_toks if t in q_set)
                scores.append(float(overlap) / max(len(doc_toks), 1))

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for rank, idx in enumerate(ranked_indices, start=1):
            results.append((self.documents[idx], float(scores[idx]), rank))
        return results

    def search_dense(self, query: str, top_k: int = 15) -> List[Tuple[Dict[str, Any], float, int]]:
        """Perform Dense vector search returning (doc, score, rank)."""
        if self.dense_model is None or self.doc_embeddings is None:
            # Fallback to BM25 if dense model is unavailable
            return self.search_bm25(query, top_k=top_k)

        import numpy as np
        query_emb = self.dense_model.encode([query], normalize_embeddings=True)[0]
        similarities = np.dot(self.doc_embeddings, query_emb)
        ranked_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, start=1):
            results.append((self.documents[idx], float(similarities[idx]), rank))
        return results

    def hybrid_search(self, query: str, top_k: int = 10, k_rrf: int = 60) -> List[Dict[str, Any]]:
        """
        Merge BM25 and Dense search using Reciprocal Rank Fusion (RRF).
        RRF Score = 1 / (k + rank_bm25) + 1 / (k + rank_dense)
        """
        bm25_hits = self.search_bm25(query, top_k=top_k * 2)
        dense_hits = self.search_dense(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        bm25_ranks: Dict[str, int] = {}
        dense_ranks: Dict[str, int] = {}

        for doc, score, rank in bm25_hits:
            doc_id = doc["id"]
            bm25_ranks[doc_id] = rank
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k_rrf + rank))

        for doc, score, rank in dense_hits:
            doc_id = doc["id"]
            dense_ranks[doc_id] = rank
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k_rrf + rank))

        sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda d_id: rrf_scores[d_id], reverse=True)[:top_k]

        merged_candidates = []
        for rank, doc_id in enumerate(sorted_doc_ids, start=1):
            doc = self.doc_map[doc_id].copy()
            doc["hybrid_rank"] = rank
            doc["bm25_rank"] = bm25_ranks.get(doc_id, 999)
            doc["dense_rank"] = dense_ranks.get(doc_id, 999)
            doc["rrf_score"] = round(rrf_scores[doc_id], 4)
            merged_candidates.append(doc)

        return merged_candidates
