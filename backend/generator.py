"""
Clinical Evidence Generator for MedVerify.
Produces structured clinical answers with strict inline [PMID: ...] citations.
"""

import time
import logging
from typing import List, Dict, Any
from gemini_client import GeminiClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are MedVerify, a clinical research AI copilot for physicians and pharmacologists.
Your responsibility is to synthesize clear, evidence-backed answers to clinical trial questions.

STRICT CLINICAL RULES:
1. Every factual proposition or recommendation MUST be followed by an inline citation: [PMID: ...].
2. Rely strictly on the provided RETRIEVED CLINICAL EVIDENCE.
3. If evidence is lacking or inconclusive, explicitly state: "Evidence is inconclusive based on available literature."
4. Do NOT hallucinate dosages, trial end-points, or mortality hazard ratios.
"""

DIRECT_SYSTEM_PROMPT = """You are MedVerify, a clinical medical AI copilot.
Provide a clear, accurate, concise explanation using established medical and physiological knowledge.

STRICT RULES:
1. Do NOT include any [PMID: ...] citations, fake PubMed IDs, or [PMID: N/A] tags.
2. Keep the response factual, clinically accurate, and concise (3 to 5 clear sentences).
"""


class ClinicalGenerator:
    def __init__(self, gemini_client: GeminiClient = None):
        self.gemini = gemini_client or GeminiClient()

    def generate(
        self,
        query: str,
        context_docs: List[Dict[str, Any]] = None,
        force_clinical_prompt: bool = False
    ) -> Dict[str, Any]:
        """Generate evidence-grounded answer given query and context."""
        start_time = time.time()
        context_docs = context_docs or []

        # Format evidence dossier
        if context_docs:
            evidence_str = ""
            for i, doc in enumerate(context_docs, start=1):
                pmid = doc.get("pmid", "UNKNOWN")
                abstract = doc.get("abstract", "")
                evidence_str += f"\n--- Evidence [{i}] (PMID: {pmid}) ---\n{abstract}\n"
            instruction_note = "Provide an evidence-grounded clinical synthesis adhering strictly to the citation format [PMID: ...]:"
            sys_prompt = SYSTEM_PROMPT
        elif force_clinical_prompt:
            # Used for No-RAG clinical trial baseline comparison
            evidence_str = "No external literature retrieved."
            instruction_note = "Answer the clinical question concisely."
            sys_prompt = SYSTEM_PROMPT
        else:
            evidence_str = "No external literature retrieved. (Direct parametric definition mode)."
            instruction_note = "Provide a concise, authoritative clinical definition using established medical knowledge. Do not include any [PMID: ...] tags."
            sys_prompt = DIRECT_SYSTEM_PROMPT

        prompt = (
            f"CLINICAL QUESTION:\n{query}\n\n"
            f"RETRIEVED CLINICAL EVIDENCE:\n{evidence_str}\n\n"
            f"{instruction_note}"
        )

        res = self.gemini.generate_text(prompt, system_instruction=sys_prompt, temperature=0.1)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "answer": res["text"],
            "prompt_tokens": res["prompt_tokens"],
            "completion_tokens": res["completion_tokens"],
            "total_tokens": res["total_tokens"],
            "latency_ms": latency_ms
        }
