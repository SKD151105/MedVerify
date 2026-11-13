"""
Adaptive Retrieval Gate for MedVerify.
Classifies clinical queries to decide whether retrieval is necessary,
single-hop clinical evidence is required, or multi-hop decomposition is needed.
"""

import time
import re
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# Definitional keywords that often do not require PubMed abstract retrieval
DEFINITIONAL_TRIGGERS = [
    r"^what is\b", r"^what are\b", r"^define\b", r"^definition of\b",
    r"^meaning of\b", r"^what does .* stand for\b"
]

# Comparative / Multi-hop indicators
COMPARATIVE_TRIGGERS = [
    r"\bcompare\b", r"\bversus\b", r"\bvs\.?\b", r"\bdifference between\b",
    r"\band .* co-administered\b", r"\bdrug interaction\b", r"\bcombined with\b"
]

# Clinical evidence triggers (efficacy, safety, dosing, clinical trials)
CLINICAL_TRIGGERS = [
    r"\bdoes\b", r"\befficacy\b", r"\bmortality\b", r"\brisk of\b",
    r"\btrial\b", r"\brandomized\b", r"\bdosage\b", r"\bdose adjustment\b",
    r"\bpatients with\b", r"\btreatment\b", r"\btherapy\b", r"\breduce\b"
]


class AdaptiveRouter:
    def __init__(self, confidence_threshold: float = 0.80):
        self.confidence_threshold = confidence_threshold

    def route(self, query: str) -> Dict[str, Any]:
        """
        Analyze query and return routing decision with confidence and telemetry.
        Possible routes:
        - DIRECT_ANSWER: Parametric memory is sufficient.
        - CLINICAL_RETRIEVAL: Evidence-backed single-hop retrieval required.
        - MULTI_HOP: Multi-entity / comparative reasoning required.
        """
        start_time = time.time()
        q_clean = query.strip().lower()

        # Check for multi-hop / comparative
        is_multihop = any(re.search(pat, q_clean) for pat in COMPARATIVE_TRIGGERS)
        if is_multihop:
            sub_queries = self._decompose_query(query)
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "route": "MULTI_HOP",
                "confidence": 0.92,
                "reasoning": "Detected comparative clinical entities or drug-drug interaction requiring multi-hop synthesis.",
                "sub_queries": sub_queries,
                "requires_retrieval": True,
                "decision_latency_ms": latency_ms
            }

        # Check for definitional query (candidate for Direct Answer / No-RAG)
        is_definitional = any(re.search(pat, q_clean) for pat in DEFINITIONAL_TRIGGERS)
        is_clinical_evidence = any(re.search(pat, q_clean) for pat in CLINICAL_TRIGGERS)

        if is_definitional and not is_clinical_evidence:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "route": "DIRECT_ANSWER",
                "confidence": 0.88,
                "reasoning": "Query is a standard medical definition or conceptual query. Parametric LLM memory suffices.",
                "sub_queries": [query],
                "requires_retrieval": False,
                "decision_latency_ms": latency_ms
            }

        # Default to Clinical Retrieval
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "route": "CLINICAL_RETRIEVAL",
            "confidence": 0.95,
            "reasoning": "Specific clinical efficacy, trial outcome, or dosing question detected. PubMed evidence retrieval is required.",
            "sub_queries": [query],
            "requires_retrieval": True,
            "decision_latency_ms": latency_ms
        }

    def _decompose_query(self, query: str) -> List[str]:
        """Decomposes comparative query into sub-queries."""
        sub_queries = [query]
        if "vs" in query.lower() or "versus" in query.lower():
            parts = re.split(r"\b(?:vs\.?|versus)\b", query, flags=re.IGNORECASE)
            if len(parts) == 2:
                sub_queries.extend([f"Clinical pharmacology and outcomes of {parts[0].strip()}",
                                    f"Clinical pharmacology and outcomes of {parts[1].strip()}"])
        elif "and" in query.lower() and "co-administered" in query.lower():
            sub_queries.append(f"Pharmacokinetics and drug interaction for {query}")
        return sub_queries
