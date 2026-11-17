"""
Adaptive Retrieval Gate for MedVerify.
Decides WHEN to retrieve: Direct Parametric vs Single-Hop vs Multi-Hop.
"""

import re
import time
import logging
from typing import Dict, Any, List
from gemini_client import GeminiClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFINITIONAL_PATTERNS = [
    r"^what is\b", r"^what are\b", r"^define\b", r"^definition of\b",
    r"^meaning of\b", r"^what does .* stand for\b"
]

COMPARATIVE_PATTERNS = [
    r"\bcompare\b", r"\bversus\b", r"\bvs\.?\b", r"\bdifference between\b",
    r"\band .* co-administered\b", r"\bdrug interaction\b", r"\bcombined with\b"
]

CLINICAL_PATTERNS = [
    r"\bdoes\b", r"\befficacy\b", r"\bmortality\b", r"\brisk of\b",
    r"\btrial\b", r"\brandomized\b", r"\bdosage\b", r"\bdose adjustment\b",
    r"\bpatients with\b", r"\btreatment\b", r"\btherapy\b", r"\breduce\b"
]


class AdaptiveRouter:
    def __init__(self, gemini_client: GeminiClient = None):
        self.gemini = gemini_client or GeminiClient()

    def route(self, query: str) -> Dict[str, Any]:
        """
        Analyze query and return routing action with reasoning, confidence, and latency.
        """
        start_time = time.time()
        q_lower = query.strip().lower()

        # Check for comparative / multi-hop
        is_comparative = any(re.search(pat, q_lower) for pat in COMPARATIVE_PATTERNS)
        if is_comparative:
            sub_queries = self._decompose(query)
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "route": "MULTI_HOP",
                "confidence": 0.94,
                "reasoning": "Detected comparative entities or drug-drug interaction requiring multi-hop synthesis.",
                "sub_queries": sub_queries,
                "requires_retrieval": True,
                "decision_latency_ms": latency_ms
            }

        # Check for definitional query (candidate for Direct Answer / No-RAG)
        is_definitional = any(re.search(pat, q_lower) for pat in DEFINITIONAL_PATTERNS)
        is_clinical = any(re.search(pat, q_lower) for pat in CLINICAL_PATTERNS)

        if is_definitional and not is_clinical:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "route": "DIRECT_ANSWER",
                "confidence": 0.91,
                "reasoning": "Query is a standard medical definition or conceptual term. Parametric memory suffices (Zero retrieval).",
                "sub_queries": [query],
                "requires_retrieval": False,
                "decision_latency_ms": latency_ms
            }

        # Default to Clinical Retrieval
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "route": "CLINICAL_RETRIEVAL",
            "confidence": 0.96,
            "reasoning": "Clinical trial evidence, drug efficacy, or dosing question detected. PubMed retrieval required.",
            "sub_queries": [query],
            "requires_retrieval": True,
            "decision_latency_ms": latency_ms
        }

    def _decompose(self, query: str) -> List[str]:
        """Decomposes comparative query into sub-queries."""
        sub_queries = [query]
        if "vs" in query.lower() or "versus" in query.lower():
            parts = re.split(r"\b(?:vs\.?|versus)\b", query, flags=re.IGNORECASE)
            if len(parts) == 2:
                sub_queries.extend([
                    f"Clinical outcomes and pharmacology of {parts[0].strip()}",
                    f"Clinical outcomes and pharmacology of {parts[1].strip()}"
                ])
        elif "and" in query.lower() and "co-administered" in query.lower():
            sub_queries.append(f"Pharmacokinetics and drug interaction for {query}")
        return sub_queries
