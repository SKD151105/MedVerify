"""
End-to-End Pipeline Orchestrator for MedVerify.
Executes Adaptive RAG + Reranking + Hallucination Guardrail and side-by-side 3-way benchmarks.
"""

import time
import logging
from typing import Dict, Any, List

from config import RAW_RETRIEVAL_TOP_K, RERANKED_TOP_K, FIXED_RAG_TOP_K
from gemini_client import GeminiClient
from router import AdaptiveRouter
from retriever import HybridRetriever
from reranker import CrossReranker
from generator import ClinicalGenerator
from verifier import HallucinationVerifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class MedVerifyPipeline:
    def __init__(self, gemini_client: GeminiClient = None):
        self.gemini = gemini_client or GeminiClient()
        self.router = AdaptiveRouter(self.gemini)
        self.retriever = HybridRetriever()
        self.reranker = CrossReranker(self.gemini)
        self.generator = ClinicalGenerator(self.gemini)
        self.verifier = HallucinationVerifier(self.gemini)

    def run_adaptive_pipeline(self, query: str) -> Dict[str, Any]:
        """Execute the full MedVerify Adaptive RAG pipeline."""
        start_time = time.time()

        # 1. Routing Gate
        route_info = self.router.route(query)
        requires_retrieval = route_info["requires_retrieval"]

        retrieval_ms = 0.0
        rerank_ms = 0.0
        raw_candidates: List[Dict[str, Any]] = []
        reranked_docs: List[Dict[str, Any]] = []
        rerank_telemetry: Dict[str, Any] = {}

        # 2. Hybrid Search & Neural Rerank
        if requires_retrieval:
            t0 = time.time()
            raw_candidates = self.retriever.hybrid_search(query, top_k=RAW_RETRIEVAL_TOP_K)
            retrieval_ms = round((time.time() - t0) * 1000, 2)

            t1 = time.time()
            reranked_docs, rerank_telemetry = self.reranker.rerank(
                query, raw_candidates, top_k=RERANKED_TOP_K
            )
            rerank_ms = round((time.time() - t1) * 1000, 2)

        # 3. Clinical Synthesis
        gen_res = self.generator.generate(query, context_docs=reranked_docs)

        # 4. Claim-Level Hallucination Verification
        audit_res = self.verifier.audit_answer(gen_res["answer"], context_docs=reranked_docs)

        # 5. Telemetry & Baseline Savings Calculation
        # In Fixed-RAG, top 5 full abstracts are stuffed blindly
        fixed_estimated_tokens = sum(len(d.get("abstract", "").split()) for d in raw_candidates[:FIXED_RAG_TOP_K]) + len(query.split()) + 60
        if not requires_retrieval:
            fixed_estimated_tokens = gen_res["total_tokens"] * 3  # Fixed RAG would have retrieved blindly

        actual_tokens = gen_res["total_tokens"]
        tokens_saved = max(0, fixed_estimated_tokens - actual_tokens)
        pct_saved = round((tokens_saved / max(fixed_estimated_tokens, 1)) * 100, 1)

        total_latency_s = round(time.time() - start_time, 2)

        latency_waterfall = {
            "Routing Gate": route_info["decision_latency_ms"],
            "Hybrid Retrieval": retrieval_ms,
            "Neural Reranking": rerank_ms,
            "Clinical Synthesis": gen_res["latency_ms"],
            "NLI Verification": audit_res["latency_ms"]
        }

        return {
            "query": query,
            "final_answer": audit_res["revised_answer"],
            "raw_generated_answer": gen_res["answer"],
            "routing": route_info,
            "reranked_docs": reranked_docs,
            "rerank_telemetry": rerank_telemetry,
            "audit_result": audit_res,
            "faithfulness_score": audit_res["faithfulness_score"],
            "tokens_consumed": actual_tokens,
            "tokens_saved_percentage": pct_saved,
            "latency_waterfall": latency_waterfall,
            "total_latency_s": total_latency_s
        }

    def run_3way_benchmark(self, query: str) -> Dict[str, Any]:
        """
        Runs the exact query across 3 paradigms:
        1. No-RAG (Parametric LLM)
        2. Fixed-RAG (Naive Blind Top-5)
        3. MedVerify (Adaptive + Reranker + Guardrail)
        """
        # 1. No-RAG
        t0 = time.time()
        no_rag_gen = self.generator.generate(query, context_docs=[])
        no_rag_audit = self.verifier.audit_answer(no_rag_gen["answer"], context_docs=[])
        no_rag_time = round(time.time() - t0, 2)

        # 2. Fixed-RAG (Blind Top-5)
        t1 = time.time()
        fixed_candidates = self.retriever.hybrid_search(query, top_k=FIXED_RAG_TOP_K)
        fixed_gen = self.generator.generate(query, context_docs=fixed_candidates)
        fixed_audit = self.verifier.audit_answer(fixed_gen["answer"], context_docs=fixed_candidates)
        fixed_time = round(time.time() - t1, 2)

        # 3. MedVerify (Adaptive Pipeline)
        medverify_res = self.run_adaptive_pipeline(query)

        return {
            "query": query,
            "no_rag": {
                "name": "No-RAG (Parametric)",
                "answer": no_rag_gen["answer"],
                "faithfulness": no_rag_audit["faithfulness_score"],
                "hallucinations_detected": no_rag_audit["contradicted_claims"],
                "total_tokens": no_rag_gen["total_tokens"],
                "latency_s": no_rag_time,
                "retrieved_passages": 0
            },
            "fixed_rag": {
                "name": "Fixed-RAG (Naive Top-5)",
                "answer": fixed_gen["answer"],
                "faithfulness": fixed_audit["faithfulness_score"],
                "hallucinations_detected": fixed_audit["contradicted_claims"],
                "total_tokens": fixed_gen["total_tokens"],
                "latency_s": fixed_time,
                "retrieved_passages": len(fixed_candidates)
            },
            "medverify": {
                "name": "MedVerify (Adaptive)",
                "answer": medverify_res["final_answer"],
                "faithfulness": medverify_res["audit_result"]["faithfulness_score"],
                "hallucinations_detected": medverify_res["audit_result"]["contradicted_claims"],
                "total_tokens": medverify_res["tokens_consumed"],
                "latency_s": medverify_res["total_latency_s"],
                "retrieved_passages": len(medverify_res["reranked_docs"]),
                "tokens_saved_pct": medverify_res["tokens_saved_percentage"],
                "route_taken": medverify_res["routing"]["route"]
            }
        }
