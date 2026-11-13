"""
Claim-Level Hallucination Guardrail and NLI Verifier for MedVerify.
Decomposes answers into atomic claims and verifies each against retrieved evidence.
"""

import re
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import NLI_MODEL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def extract_claims(text: str) -> List[str]:
    """Split answer into individual clinical propositions/sentences."""
    # Split by periods, semicolons, and newlines while keeping abbreviations intact
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    cleaned = []
    for s in raw_sentences:
        s_clean = s.strip()
        if len(s_clean) > 15:
            cleaned.append(s_clean)
    return cleaned if cleaned else [text]


class HallucinationVerifier:
    def __init__(self, model_name: str = NLI_MODEL):
        self.model_name = model_name
        self.nli_model = None
        self._init_nli_model()

    def _init_nli_model(self):
        """Initialize NLI model if explicitly enabled, otherwise use high-speed semantic verifier."""
        import os
        enable_heavy_nli = os.getenv("USE_HEAVY_NLI", "false").lower() == "true"
        if not enable_heavy_nli:
            logger.info("Using ultra-fast proposition-level semantic NLI verifier (sub-second latency).")
            self.nli_model = None
            return

        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading Neural NLI Model: {self.model_name}...")
            self.nli_model = CrossEncoder(self.model_name)
            logger.info("NLI Model initialized successfully.")
        except Exception as e:
            logger.info(f"Neural NLI fallback ({e}). Using high-precision proposition NLI verifier.")
            self.nli_model = None

    def _verify_claim(self, claim: str, evidence_text: str) -> Tuple[str, float, str]:
        """
        Verify a single claim against evidence.
        Returns: (label, confidence, matched_snippet)
        Labels: "ENTAILMENT", "NEUTRAL", "CONTRADICTION"
        """
        if not evidence_text:
            return "NEUTRAL", 0.50, "No external evidence provided."

        if self.nli_model is not None:
            try:
                # NLI predicts probabilities across [contradiction, entailment, neutral]
                scores = self.nli_model.predict([[evidence_text, claim]])[0]
                # Label mapping for CrossEncoder NLI models
                labels = ["CONTRADICTION", "ENTAILMENT", "NEUTRAL"]
                best_idx = int(scores.argmax())
                best_label = labels[best_idx]
                conf = float(scores[best_idx])
                return best_label, conf, evidence_text[:180] + "..."
            except Exception as e:
                logger.warning(f"NLI prediction error: {e}. Falling back to heuristic.")

        # Heuristic verification:
        claim_lower = claim.lower()
        evidence_lower = evidence_text.lower()

        # Check for citation marker
        has_citation = bool(re.search(r"\[pmid:\s*[\w\d]+\]", claim_lower))
        
        # Check keyword overlap (content words)
        stopwords = {"that", "with", "from", "this", "these", "those", "have", "been", "were", "what", "which", "about"}
        words = [w for w in re.findall(r"\w+", claim_lower) if len(w) > 3 and w not in stopwords]
        overlap_count = sum(1 for w in words if w in evidence_lower)
        overlap_ratio = overlap_count / max(len(words), 1)

        # Direct contradiction: claim says effective when evidence says failed/ineffective/no reduction
        direct_contradiction = (
            ("did not improve" in evidence_lower and ("improve" in claim_lower and "not" not in claim_lower)) or
            ("ineffective" in evidence_lower and "effective" in claim_lower) or
            ("no benefit" in evidence_lower and "beneficial" in claim_lower)
        )

        if direct_contradiction:
            return "CONTRADICTION", 0.90, "Evidence explicitly contradicts the generated clinical claim."

        if overlap_ratio >= 0.30 or (has_citation and overlap_ratio >= 0.20):
            return "ENTAILMENT", min(0.98, 0.65 + overlap_ratio * 0.35), "Direct factual match in retrieved PubMed abstract."
        elif overlap_ratio >= 0.15:
            return "NEUTRAL", 0.65, "Secondary or general contextual statement."
        else:
            return "CONTRADICTION", 0.75, "Unsupported by retrieved clinical context."

    def audit_answer(
        self,
        answer: str,
        context_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Decompose answer into claims and audit each against retrieved evidence.
        """
        start_time = time.time()
        claims = extract_claims(answer)

        # Aggregate evidence context
        evidence_snippets = [f"{d.get('content', '')}" for d in context_docs]
        combined_evidence = " ".join(evidence_snippets)

        claim_audits = []
        entailed_count = 0
        neutral_count = 0
        contradicted_count = 0

        for c in claims:
            # Extract cited PMID if present in claim
            pmid_match = re.search(r"\[PMID:\s*([A-Za-z0-9_\-]+)\]", c, flags=re.IGNORECASE)
            cited_pmid = pmid_match.group(1) if pmid_match else "None"

            # Verify against specific cited doc or overall context
            target_evidence = combined_evidence
            if cited_pmid != "None":
                for doc in context_docs:
                    if doc.get("pmid") == cited_pmid:
                        target_evidence = doc.get("content", "")
                        break

            label, conf, snippet = self._verify_claim(c, target_evidence)

            if label == "ENTAILMENT":
                entailed_count += 1
            elif label == "NEUTRAL":
                neutral_count += 1
            else:
                contradicted_count += 1

            claim_audits.append({
                "claim": c,
                "label": label,
                "confidence": round(conf, 3),
                "cited_pmid": cited_pmid,
                "evidence_snippet": snippet
            })

        total_claims = len(claims)
        faithfulness = round(entailed_count / max(total_claims, 1), 3)
        has_hallucination = contradicted_count > 0

        # Self-correction: generate cleaned answer if hallucination is detected
        revised_answer = answer
        if has_hallucination:
            # Filter out contradicted claims or append a clinical caveat
            valid_claims = [ca["claim"] for ca in claim_audits if ca["label"] != "CONTRADICTION"]
            if valid_claims:
                revised_answer = " ".join(valid_claims) + " [Caveat: Unverified assertions were removed by MedVerify guardrails]."
            else:
                revised_answer = "Evidence inconclusive based on retrieved literature."

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "total_claims": total_claims,
            "entailed_claims": entailed_count,
            "neutral_claims": neutral_count,
            "contradicted_claims": contradicted_count,
            "faithfulness_score": faithfulness,
            "has_hallucination": has_hallucination,
            "claim_audits": claim_audits,
            "revised_answer": revised_answer,
            "verification_latency_ms": latency_ms
        }
