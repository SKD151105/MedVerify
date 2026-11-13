"""
End-to-End Pipeline Orchestrator for MedVerify.
Executes the Adaptive RAG + Reranking + Hallucination Guardrail workflow,
and runs side-by-side comparisons against No-RAG and Fixed-RAG baselines.
"""

import time
import logging
from typing import Dict, Any, List

from config import RAW_RETRIEVAL_TOP_K, RERANKED_TOP_K, FIXED_RAG_TOP_K
from src.data_loader import PubMedDataLoader
from src.vector_store import HybridRetriever
from src.reranker import NeuralReranker
from src.adaptive_router import AdaptiveRouter
from src.generator import ClinicalGenerator
from src.verifier import HallucinationVerifier
from src.telemetry import TelemetryTracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class MedVerifyPipeline:
    def __init__(self, data_path: str = None, llm_provider: str = None, api_key: str = None):
        # 1. Load Data
        self.loader = PubMedDataLoader(data_path=data_path)
        self.documents = self.loader.load_documents()

        # 2. Initialize Retriever
        self.retriever = HybridRetriever(self.documents)

        # 3. Initialize Neural Reranker
        self.reranker = NeuralReranker()

        # 4. Initialize Adaptive Router
        self.router = AdaptiveRouter()

        # 5. Initialize Generator
        self.generator = ClinicalGenerator(provider=llm_provider, api_key=api_key)

        # 6. Initialize Hallucination Verifier
        self.verifier = HallucinationVerifier()

    def run_adaptive_pipeline(self, query: str) -> Dict[str, Any]:
        """Execute the full MedVerify Adaptive RAG pipeline."""
        pipeline_start = time.time()

        # Step 1: Adaptive Routing Gate
        route_info = self.router.route(query)
        requires_retrieval = route_info["requires_retrieval"]

        retrieval_ms = 0.0
        rerank_ms = 0.0
        raw_candidates: List[Dict[str, Any]] = []
        reranked_docs: List[Dict[str, Any]] = []
        rerank_telemetry: Dict[str, Any] = {}

        # Step 2: Hybrid Retrieval & Cross-Encoder Reranking
        if requires_retrieval:
            retrieval_start = time.time()
            raw_candidates = self.retriever.hybrid_search(query, top_k=RAW_RETRIEVAL_TOP_K)
            retrieval_ms = round((time.time() - retrieval_start) * 1000, 2)

            rerank_start = time.time()
            reranked_docs, rerank_telemetry = self.reranker.rerank(
                query, raw_candidates, top_k=RERANKED_TOP_K
            )
            rerank_ms = round((time.time() - rerank_start) * 1000, 2)

        # Step 3: Clinical Generation
        gen_result = self.generator.generate(query, context_docs=reranked_docs)
        raw_answer = gen_result["answer"]
        gen_tokens = gen_result["total_tokens"]

        # Step 4: Claim-Level Hallucination Verification
        audit_result = self.verifier.audit_answer(raw_answer, context_docs=reranked_docs)

        # Step 5: Compute Telemetry & Cost Savings vs Fixed Baseline
        fixed_estimated_tokens = (
            sum(len(d.get("content", "").split()) for d in raw_candidates[:FIXED_RAG_TOP_K])
            + len(query.split()) + 60
        ) if requires_retrieval else gen_tokens * 2

        cost_savings = TelemetryTracker.calculate_cost_savings(
            tokens_adaptive=gen_tokens,
            tokens_fixed=fixed_estimated_tokens
        )

        latency_waterfall = TelemetryTracker.compile_latency_waterfall(
            routing_ms=route_info["decision_latency_ms"],
            retrieval_ms=retrieval_ms,
            reranking_ms=rerank_ms,
            generation_ms=gen_result["latency_ms"],
            verification_ms=audit_result["verification_latency_ms"]
        )

        ragas_card = TelemetryTracker.calculate_ragas_scorecard(
            faithfulness=audit_result["faithfulness_score"],
            retained_docs_count=len(reranked_docs),
            query=query,
            answer=audit_result["revised_answer"]
        )

        return {
            "query": query,
            "final_answer": audit_result["revised_answer"],
            "raw_generated_answer": raw_answer,
            "routing": route_info,
            "raw_candidates_count": len(raw_candidates),
            "reranked_docs": reranked_docs,
            "rerank_telemetry": rerank_telemetry,
            "audit_result": audit_result,
            "cost_savings": cost_savings,
            "latency_waterfall": latency_waterfall,
            "ragas_scorecard": ragas_card,
            "total_execution_time_s": round(time.time() - pipeline_start, 2)
        }

    def run_baseline_comparison(self, query: str) -> Dict[str, Any]:
        """
        Runs the exact query across 3 paradigms:
        1. No-RAG (Parametric LLM)
        2. Fixed-RAG (Blind top-5 retrieval, no reranking, no verification)
        3. MedVerify (Adaptive RAG + Reranker + Guardrail)
        """
        # Baseline 1: No-RAG
        no_rag_start = time.time()
        no_rag_gen = self.generator.generate(query, context_docs=[])
        no_rag_audit = self.verifier.audit_answer(no_rag_gen["answer"], context_docs=[])
        no_rag_time = round(time.time() - no_rag_start, 2)

        # Baseline 2: Fixed-RAG
        fixed_rag_start = time.time()
        fixed_candidates = self.retriever.hybrid_search(query, top_k=FIXED_RAG_TOP_K)
        fixed_gen = self.generator.generate(query, context_docs=fixed_candidates)
        fixed_audit = self.verifier.audit_answer(fixed_gen["answer"], context_docs=fixed_candidates)
        fixed_time = round(time.time() - fixed_rag_start, 2)

        # MedVerify Adaptive
        medverify_result = self.run_adaptive_pipeline(query)

        return {
            "query": query,
            "no_rag": {
                "answer": no_rag_gen["answer"],
                "faithfulness": no_rag_audit["faithfulness_score"],
                "total_tokens": no_rag_gen["total_tokens"],
                "latency_s": no_rag_time,
                "retrieved_docs_count": 0,
                "hallucinations_detected": no_rag_audit["contradicted_claims"]
            },
            "fixed_rag": {
                "answer": fixed_gen["answer"],
                "faithfulness": fixed_audit["faithfulness_score"],
                "total_tokens": fixed_gen["total_tokens"],
                "latency_s": fixed_time,
                "retrieved_docs_count": len(fixed_candidates),
                "hallucinations_detected": fixed_audit["contradicted_claims"]
            },
            "medverify": {
                "answer": medverify_result["final_answer"],
                "faithfulness": medverify_result["audit_result"]["faithfulness_score"],
                "total_tokens": medverify_result["cost_savings"]["tokens_adaptive"],
                "latency_s": medverify_result["total_execution_time_s"],
                "retrieved_docs_count": len(medverify_result["reranked_docs"]),
                "hallucinations_detected": medverify_result["audit_result"]["contradicted_claims"],
                "route_taken": medverify_result["routing"]["route"],
                "tokens_saved_pct": medverify_result["cost_savings"]["percentage_tokens_saved"]
            }
        }
