"""
Robust Unified Gemini Client for Text Generation, Structured JSON, and Embeddings.
Uses Google's REST API with automatic retries and fallback models.
"""

import json
import logging
import urllib.request
import urllib.error
import time
from typing import Dict, Any, List, Optional
from config import GEMINI_API_KEY, GEMINI_MODEL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Verified fast active models for this API key
MODEL_FALLBACKS = [
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest"
]


class GeminiClient:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY provided. Gemini client running in limited mode.")

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Generate text using Gemini REST API with model fallbacks."""
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        data_bytes = json.dumps(payload).encode("utf-8")

        for model_name in MODEL_FALLBACKS:
            clean_model = model_name.replace("models/", "")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}"
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    candidates = res_json.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text = "".join(p.get("text", "") for p in parts)
                        usage = res_json.get("usageMetadata", {})
                        return {
                            "text": text.strip(),
                            "prompt_tokens": usage.get("promptTokenCount", len(prompt.split())),
                            "completion_tokens": usage.get("candidatesTokenCount", len(text.split())),
                            "total_tokens": usage.get("totalTokenCount", len(prompt.split()) + len(text.split())),
                            "model_used": clean_model
                        }
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                logger.warning(f"Gemini call to {clean_model} returned {e.code}: {err_body[:120]}. Trying next fallback...")
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Error calling {clean_model}: {e}. Trying next fallback...")
                time.sleep(0.5)

        # Fallback return if all fail
        return {
            "text": "Unable to complete request via Gemini API at this time.",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model_used": "failed"
        }

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON response."""
        full_system = (system_instruction or "") + "\n\nCRITICAL: Output ONLY valid raw JSON with NO markdown backticks or explanation."
        res = self.generate_text(prompt, system_instruction=full_system, temperature=0.1)
        raw_text = res["text"].strip()

        # Clean markdown codeblocks if model included them
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("\n", 1)[0]
        raw_text = raw_text.strip()

        try:
            parsed = json.loads(raw_text)
            return {"data": parsed, "tokens": res["total_tokens"], "model": res["model_used"]}
        except Exception:
            logger.warning(f"Could not parse Gemini JSON output: {raw_text[:100]}...")
            return {"data": {}, "tokens": res["total_tokens"], "model": res["model_used"]}
