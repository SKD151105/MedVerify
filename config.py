"""
Configuration settings for MedVerify: Adaptive RAG & Clinical Hallucination Guardrails.
"""

import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Directories
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
LOGS_DIR = PROJECT_ROOT / "logs"

DATA_DIR.mkdir(exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Set HuggingFace Cache to D: drive (C: drive is out of disk space)
HF_CACHE_DIR = DATA_DIR / "hf_cache"
HF_CACHE_DIR.mkdir(exist_ok=True)
os.environ["HF_HOME"] = str(HF_CACHE_DIR)
os.environ["TRANSFORMERS_CACHE"] = str(HF_CACHE_DIR)

# Datasets
PUBMEDQA_FILE = DATA_DIR / "pubmedqa_labeled.json"
SAMPLE_DATA_FILE = DATA_DIR / "sample_data.json"

# Models & Embeddings
DENSE_EMBEDDING_MODEL = os.getenv("DENSE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
NLI_MODEL = os.getenv("NLI_MODEL", "cross-encoder/nli-deberta-v3-small")

# Retrieval Parameters
RAW_RETRIEVAL_TOP_K = 10      # Number of candidates from hybrid search
RERANKED_TOP_K = 3            # Top candidates retained after cross-encoder reranking
RERANK_SCORE_THRESHOLD = 0.20 # Minimum normalized score to retain a chunk

# Adaptive Router Thresholds
ROUTER_CONFIDENCE_THRESHOLD = 0.80  # Above this, simple definitional queries skip retrieval

# LLM Configurations
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini") # "gemini", "openai", or "mock"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.1

# Vector Database Settings
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "hybrid_local") # "hybrid_local", "chroma", or "pinecone"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "medverify-pubmedqa")

# Baselines Configuration
FIXED_RAG_TOP_K = 5           # Naive fixed RAG uses a static top-k without reranking or verification
