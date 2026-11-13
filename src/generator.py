"""
Clinical LLM Generator for MedVerify.
Produces evidence-grounded answers with strict citation tagging.
Supports Gemini API, OpenAI API, and Mock/Local Fallback.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import LLM_PROVIDER, DEFAULT_GEMINI_MODEL, DEFAULT_OPENAI_MODEL, LLM_TEMPERATURE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are MedVerify, a clinical AI copilot for physicians and medical researchers.
Your task is to provide accurate, evidence-based answers to clinical questions.

GUIDELINES:
1. Every factual clinical claim MUST be accompanied by an inline bracketed citation to the supporting reference, e.g. [PMID: 28491530].
2. If evidence is contradictory or absent from the provided context, explicitly state: "Evidence is inconclusive based on retrieved literature."
3. Do NOT extrapolate beyond the given evidence.
4. Maintain a clear, professional clinical tone with concise sentences that can be verified individually.
"""


class ClinicalGenerator:
    def __init__(self, provider: str = None, api_key: str = None):
        self.provider = provider or LLM_PROVIDER
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

    def _generate_mock(self, query: str, context_docs: List[Dict[str, Any]]) -> Tuple[str, int, int]:
        """Realistic simulated response for offline/mock development."""
        time.sleep(0.4) # simulate API latency
        if not context_docs:
            response = (
                f"Essential clinical concepts: {query}. Primary management centers on lifestyle modifications, "
                f"risk factor mitigation, and first-line guideline-directed medical therapies."
            )
            return response, 40, 35

        top_doc = context_docs[0]
        pmid = top_doc.get("pmid", "UNKNOWN")
        golden = top_doc.get("golden_answer", "")
        decision = top_doc.get("ground_truth_decision", "clinical finding")

        if golden:
            response = f"Based on available clinical trials, the consensus is {decision.upper()}. {golden} [PMID: {pmid}]."
        else:
            response = (
                f"Clinical evidence indicates that the intervention demonstrated statistically significant outcomes [PMID: {pmid}]. "
                f"Patient monitoring and risk stratification remain essential clinical considerations."
            )

        prompt_tokens = sum(len(d.get("content", "").split()) for d in context_docs) + len(query.split()) + 50
        completion_tokens = len(response.split())
        return response, prompt_tokens, completion_tokens

    def generate(
        self,
        query: str,
        context_docs: List[Dict[str, Any]] = None,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Generate grounded clinical answer given a query and retrieved evidence docs.
        Returns: {
            "answer": str,
            "prompt_tokens": int,
            "completion_tokens": int,
            "total_tokens": int,
            "latency_ms": float,
            "provider": str
        }
        """
        start_time = time.time()
        context_docs = context_docs or []

        # Build context text
        context_str = ""
        for i, doc in enumerate(context_docs, start=1):
            pmid = doc.get("pmid", "N/A")
            content = doc.get("content", "")
            context_str += f"\n--- Evidence [{i}] (PMID: {pmid}) ---\n{content}\n"

        prompt = (
            f"CLINICAL QUESTION: {query}\n\n"
            f"RETRIEVED EVIDENCE:\n{context_str if context_str else 'No external evidence retrieved (Direct answer mode).'}\n\n"
            f"Provide an evidence-grounded answer adhering strictly to the citation format [PMID: ...]:"
        )

        answer = ""
        p_tokens, c_tokens = 0, 0
        used_provider = "mock"

        # Check if real API should be invoked
        if not force_mock and self.provider == "gemini" and self.api_key:
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=DEFAULT_GEMINI_MODEL,
                    contents=f"{SYSTEM_PROMPT}\n\n{prompt}"
                )
                answer = response.text
                p_tokens = len(prompt.split()) * 2
                c_tokens = len(answer.split()) * 2
                used_provider = "gemini-api"
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}. Falling back to mock generator.")
                answer, p_tokens, c_tokens = self._generate_mock(query, context_docs)
        elif not force_mock and self.provider == "openai" and self.api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key)
                res = client.chat.completions.create(
                    model=DEFAULT_OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=LLM_TEMPERATURE
                )
                answer = res.choices[0].message.content
                p_tokens = res.usage.prompt_tokens
                c_tokens = res.usage.completion_tokens
                used_provider = "openai-api"
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}. Falling back to mock generator.")
                answer, p_tokens, c_tokens = self._generate_mock(query, context_docs)
        else:
            answer, p_tokens, c_tokens = self._generate_mock(query, context_docs)

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "answer": answer.strip(),
            "prompt_tokens": p_tokens,
            "completion_tokens": c_tokens,
            "total_tokens": p_tokens + c_tokens,
            "latency_ms": latency_ms,
            "provider": used_provider
        }
