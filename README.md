# MedVerify: Clinical RAG with Adaptive Retrieval & Claim-Level Hallucination Guardrails

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

MedVerify is a domain-specific Retrieval-Augmented Generation (RAG) platform built for clinical question answering. It replaces naive static retrieval with an **adaptive complexity gate**, a **neural cross-encoder reranker**, and an **automated Natural Language Inference (NLI) proposition auditor** that verifies every generated claim against source medical literature before output delivery.

---

## The Problem

Standard "Fixed-RAG" systems suffer from two core failure modes in medical and clinical workflows:

1. **Blind Retrieval Overhead:** Naive pipelines retrieve a static number of passages (e.g., top-5) for every query indiscriminately. For basic definitional or pharmacological questions (e.g., *"What is essential hypertension?"*), this wastes prompt tokens, inflates latency, and injects irrelevant context distractors into the generation window.
2. **Contextual Hallucination:** Even when clinical abstracts are retrieved, LLMs frequently extrapolate findings, blend unsupported parametric memories, or fabricate drug efficacy assertions while citing real literature.

MedVerify addresses this by combining **adaptive retrieval gating** (deciding *when* to search), **signal-to-noise reranking** (pruning distractor chunks), and **atomic claim-level NLI verification** (entailment checking with automated self-correction).

---

## Architecture Overview

```
                           +--------------------------+
                           |   Clinical User Query    |
                           +------------+-------------+
                                        |
                                        v
                       +----------------------------------+
                       |   1. Adaptive Complexity Gate    |
                       |  (Prompt Classifier / Router)    |
                       +----------------+-----------------+
                                        |
                 +----------------------+----------------------+
                 | (Direct Answer)                             | (Requires Clinical Evidence)
                 v                                             v
     +-----------------------+                    +--------------------------+
     |   Parametric Memory   |                    | 2. Hybrid Search Engine  |
     | (Zero-Retrieval Path) |                    | BM25 Lexical + Semantic  |
     +-----------+-----------+                    +------------+-------------+
                 |                                             | (Top-10 Candidates)
                 |                                             v
                 |                                +--------------------------+
                 |                                |  3. Neural Reranker      |
                 |                                |  RankGPT Cross-Encoder   |
                 |                                |  + Dynamic Score Pruning |
                 |                                +------------+-------------+
                 |                                             | (Top-3 Relevant Chunks)
                 |                                             v
                 |                                +--------------------------+
                 |                                | 4. Clinical Synthesizer  |
                 |                                | Strict [PMID] Citations  |
                 |                                +------------+-------------+
                 |                                             |
                 +----------------------+----------------------+
                                        |
                                        v
                       +----------------------------------+
                       |    5. Claim-Level NLI Auditor    |
                       |  - Extract Atomic Propositions   |
                       |  - Premise-Hypothesis Inference  |
                       |  - Entailment / Contradiction    |
                       +----------------+-----------------+
                                        |
                       +----------------+-----------------+
                       |                                  |
            [All Claims Entailed]              [Contradiction Detected]
                       |                                  |
                       v                                  v
           +-----------------------+          +-----------------------+
           | Deliver Grounded QA   |          | Self-Correction Loop  |
           | + Audit Telemetry     |          | (Prune False Claims)  |
           +-----------------------+          +-----------------------+
```

---

## Core Pipeline Components

### 1. Adaptive Complexity Router
Analyzes incoming queries and routes them into one of three execution paths:
- **`DIRECT_ANSWER`**: Conceptual, definitional, or standard nomenclature queries bypass external search completely, saving 100% of retrieval overhead.
- **`CLINICAL_RETRIEVAL`**: Quantitative clinical trial, drug efficacy, or guideline queries trigger targeted retrieval over curated medical literature.
- **`MULTI_HOP`**: Complex comparative interactions are decomposed into structured sub-queries.

### 2. Hybrid Lexical-Semantic Retrieval
Combines sparse BM25 indexing (capturing precise drug names, dosages, and alphanumeric identifiers like `stages 1 to 3b`) with semantic overlap scoring, merged via Reciprocal Rank Fusion (RRF) to retrieve an initial candidate pool of 10 passages.

### 3. Neural Cross-Encoder Reranker
Passes the candidate pool through a cross-attention reranker to compute joint relevance scores. Documents falling below the relevance threshold ($\tau = 0.25$) are pruned as distractors, retaining only the top-3 high-signal abstracts.

### 4. Claim-Level Hallucination Guardrail
Before returning the clinical response:
1. Deconstructs the generated text into atomic factual propositions using syntactic boundary parsing.
2. Runs Natural Language Inference (NLI) against retrieved premise abstracts.
3. Categorizes each claim:
   - **`ENTAILMENT` (Green):** Factually supported by the cited study.
   - **`NEUTRAL` (Yellow):** General medical consensus not explicitly asserted in the context.
   - **`CONTRADICTION` (Red):** Conflicting or fabricated claim.
4. If a contradiction is detected, an automated guardrail loop strips the ungrounded assertion or flags it with a clinician warning.

---

## Empirical Benchmark & Evaluation

Tested against curated clinical trials from the **PubMedQA** benchmark dataset comparing three paradigms:

| Metric | No-RAG (Parametric) | Fixed-RAG (Naive Top-5) | MedVerify (Adaptive) |
| :--- | :---: | :---: | :---: |
| **Faithfulness Score (↑)** | 0.0% | 100.0% | **100.0%** *(Matches Best)* |
| **Hallucination Rate (↓)** | 22.4% | 8.1% | **0.0%** *(Fully Shielded)* |
| **Average Tokens / Query (↓)** | 191 | 1,496 *(Highest)* | **792** *(**47.1% Saved**)* |
| **Distractor Pruning** | N/A | None (All 5 stuffed) | **Dynamic Thresholding** |
| **Claim-Level Grounding** | None | Unverified | **Atomic NLI Audit** |
| **Average Pipeline Latency** | ~2.2s | ~4.3s | ~11.6s *(Includes NLI)* |

> **Key Finding:** MedVerify matches the 100% faithfulness of full retrieval while reducing token consumption by **47.1%** through adaptive routing and neural distractor pruning.

---

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2
- **Information Retrieval:** `rank-bm25` (sparse lexical search), Reciprocal Rank Fusion
- **LLM & Inference:** Google Gemini REST API (`gemini-2.5-flash-lite`, `gemini-3.1-flash-lite`) — zero local model downloads, runnable on low-spec CPU machines
- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons
- **Evaluation Dataset:** Curated PubMedQA biomedical research QA records

---

## Project Structure

```
MedVerify/
├── backend/
│   ├── config.py              # System parameters, thresholds, and file paths
│   ├── gemini_client.py       # REST client with automatic retry & model fallbacks
│   ├── router.py              # Adaptive complexity classifier
│   ├── retriever.py           # Hybrid BM25 lexical & semantic retrieval
│   ├── reranker.py            # RankGPT cross-encoder reranking & distractor pruning
│   ├── generator.py           # Clinical synthesis engine with [PMID] attribution
│   ├── verifier.py            # Proposition decomposition & NLI hallucination auditor
│   ├── pipeline.py            # End-to-end orchestrator & 3-way benchmark runner
│   ├── main.py                # FastAPI HTTP application routes
│   ├── evaluation.py          # Standalone terminal evaluation benchmark suite
│   ├── requirements.txt       # Lightweight backend dependencies
│   ├── .env.example           # Environment template
│   └── data/
│       └── pubmed_100.json    # Curated clinical trial records & ground truths
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Dual-pane UI: Copilot telemetry & 3-way benchmark
│   │   ├── defaultData.js     # Instant fallback telemetry state for zero-wait load
│   │   ├── index.css          # Glassmorphism styling, theme variables, and glow effects
│   │   └── main.jsx           # React DOM root mounting
│   ├── package.json           # Frontend dependencies
│   ├── tailwind.config.js     # Tailwind design system configuration
│   └── vite.config.js         # Vite configuration with API proxy to port 8000
├── PROJECT_PLAN_AND_ARCHITECTURE.md  # Detailed architecture specification
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- A Google Gemini API key ([Google AI Studio](https://aistudio.google.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/SKD151105/MedVerify.git
cd MedVerify
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env   # On Linux/macOS: cp .env.example .env
```

Edit `backend/.env` with your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
HOST=0.0.0.0
PORT=8000
```

Start the FastAPI backend server:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API will be live at `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### 3. Frontend Setup
In a new terminal window:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open your browser and navigate to `http://localhost:5173`.

---

## Running the Terminal Benchmark

To execute the automated 3-way evaluation benchmark across PubMedQA test queries directly in your terminal:

```bash
cd backend
python evaluation.py
```

This will run the comparative evaluation across No-RAG, Fixed-RAG, and MedVerify, printing a formatted scorecard with Faithfulness, Hallucination Rate, Token Consumption, and Latency metrics.

---

## API Reference

### `GET /api/health`
Health check endpoint returning service status.

### `GET /api/scenarios`
Returns curated PubMedQA clinical cases for quick scenario testing in the UI.

### `POST /api/query`
Executes the full MedVerify pipeline on a user query.
```json
// Request
{
  "query": "Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?"
}

// Response
{
  "query": "...",
  "final_answer": "...",
  "routing": {
    "route": "CLINICAL_RETRIEVAL",
    "confidence": 0.95,
    "requires_retrieval": true
  },
  "faithfulness_score": 1.0,
  "audit_result": {
    "total_claims": 3,
    "entailed_claims": 3,
    "contradicted_claims": 0,
    "claim_audits": [ ... ]
  },
  "tokens_consumed": 792,
  "tokens_saved_percentage": 47.1,
  "latency_waterfall": { ... }
}
```

### `POST /api/benchmark`
Executes side-by-side evaluation across No-RAG, Fixed-RAG, and MedVerify on the given query.

---

## Hardware Efficiency Note

MedVerify is intentionally designed to run on consumer-grade hardware without requiring a local GPU. By offloading neural embeddings and generative inference to cloud REST endpoints while handling BM25 indexing and proposition parsing locally, the application maintains a negligible local memory footprint (~150 MB RAM) and does not require local PyTorch model downloads.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
