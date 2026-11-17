"""
Configuration settings for MedVerify Backend.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# Paths
DATA_DIR = BASE_DIR / "data"
PUBMED_DATA_FILE = DATA_DIR / "pubmed_100.json"
DATA_DIR.mkdir(exist_ok=True)

# Retrieval & Guardrails Parameters
RAW_RETRIEVAL_TOP_K = 10        # Hybrid pool size
RERANKED_TOP_K = 3              # After RankGPT reranking
RERANK_THRESHOLD = 0.25         # Drop distractor chunks below this score
ROUTER_CONFIDENCE_THRESHOLD = 0.85

# Baselines Configuration
FIXED_RAG_TOP_K = 5             # Naive Fixed-RAG baseline chunk count
