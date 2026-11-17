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

# Verified active models with healthy quota for this API key
MODEL_FALLBACKS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview"
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
        max_tokens: int = 1500,
        response_mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate text using Gemini REST API with model fallbacks."""
        gen_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
        if response_mime_type:
            gen_config["responseMimeType"] = response_mime_type

        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": gen_config
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
                with urllib.request.urlopen(req, timeout=25) as resp:
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
                # Rate-limit errors need a longer backoff to avoid cascading 429s
                time.sleep(2.0 if e.code == 429 else 0.5)
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
        """Generate structured JSON response with guaranteed JSON mime type and robust parsing."""
        import re
        full_system = (system_instruction or "") + "\n\nCRITICAL: Output strictly valid JSON."
        res = self.generate_text(
            prompt,
            system_instruction=full_system,
            temperature=0.1,
            max_tokens=2500,
            response_mime_type="application/json"
        )
        raw_text = res["text"].strip()

        # Clean any accidental markdown codeblock wrappers
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        # If needed, locate the outer JSON object or array
        if not (cleaned.startswith("{") or cleaned.startswith("[")):
            match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
            if match:
                cleaned = match.group(1).strip()

        # Fix unescaped backslashes (e.g. LaTeX formulas, \%, \m, \d) that cause 'Invalid \escape'
        cleaned = re.sub(r'\\([^"\\/bfnrtu]|u[0-9a-fA-F]{0,3}[^0-9a-fA-F])', r'\1', cleaned)

        try:
            parsed = json.loads(cleaned, strict=False)
            return {"data": parsed, "tokens": res["total_tokens"], "model": res["model_used"]}
        except Exception as e:
            # Fallback: aggressively sanitize backslashes and try once more
            try:
                sanitized = re.sub(r'\\', r'\\\\', cleaned)
                # revert double escaping on valid json escapes
                sanitized = re.sub(r'\\\\(["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\1', sanitized)
                parsed = json.loads(sanitized, strict=False)
                return {"data": parsed, "tokens": res["total_tokens"], "model": res["model_used"]}
            except Exception:
                pass
            logger.warning(f"Could not parse Gemini JSON output: {e} - Raw: {cleaned[:120]}...")
            return {"data": {}, "tokens": res["total_tokens"], "model": res["model_used"]}
