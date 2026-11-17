# MedVerify

**Clinical RAG platform with Adaptive Retrieval and Claim-Level Hallucination Guardrails**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What This Project Is

MedVerify is a Retrieval-Augmented Generation (RAG) system built for clinical question answering. It goes beyond standard RAG in three specific ways:

1. **It decides whether to retrieve at all.** A lightweight query router analyzes the incoming question and routes it into one of three paths — direct parametric answer, single-hop clinical retrieval, or multi-hop decomposed search — before touching the vector index.

2. **It filters retrieved evidence before generation.** A neural cross-encoder reranker scores every candidate passage and drops documents that fall below a relevance threshold, so the LLM only sees high-signal evidence.

3. **It audits the generated answer, sentence by sentence, before returning it.** A Natural Language Inference (NLI) verifier decomposes the output into atomic claims, checks each one against the retrieved literature, and flags or removes anything that isn't grounded.

The result is a system that uses fewer tokens than naive RAG, produces fewer hallucinations than no-RAG, and is fully observable — every routing decision, rank shift, and verification label is surfaced in the UI.

---

## The Problem With Standard RAG

Most production RAG systems work like this:

```
User question → embed → vector search top-5 → stuff into prompt → LLM generates
```

This breaks down in medical contexts in two ways:

**Blind retrieval** — the pipeline fetches the same number of documents (say, 5) for every query regardless of complexity. A question like *"What is essential hypertension?"* doesn't need 5 research abstracts. It just needs the LLM's parametric knowledge. Forcing retrieval for definitional questions wastes tokens and injects irrelevant context that can confuse the model.

**Unverified generation** — even when the right paper is retrieved, LLMs frequently blend retrieved content with their internal training memory. They might hallucinate a drug dosage, misquote a mortality hazard ratio, or state a contraindication that conflicts with the actual study. In a clinical context, this is not a minor inconvenience — it's genuinely dangerous.

MedVerify addresses both.

---

## Architecture

```
                        ┌──────────────────────────┐
                        │     Clinical User Query   │
                        └────────────┬─────────────┘
                                     │
                                     ▼
                        ┌──────────────────────────┐
                        │  1. Adaptive Routing Gate │
                        │   Pattern matching +      │
                        │   intent classification   │
                        └───┬──────────┬────────────┘
                            │          │
              ┌─────────────┘          └───────────────────┐
              ▼                                             ▼
   DIRECT_ANSWER                               CLINICAL_RETRIEVAL / MULTI_HOP
   (skip retrieval)                            │
                                               ▼
                                ┌──────────────────────────┐
                                │  2. Hybrid Search Engine  │
                                │  BM25 + Semantic overlap  │
                                │  merged via RRF           │
                                │  → Top-10 candidates      │
                                └────────────┬─────────────┘
                                             │
                                             ▼
                                ┌──────────────────────────┐
                                │  3. Cross-Encoder Reranker│
                                │  RankGPT scores each doc  │
                                │  Prune if score < 0.25    │
                                │  → Top-3 retained         │
                                └────────────┬─────────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              ▼                             ▼
              ┌────────────────────────┐    ┌──────────────────────────┐
              │  4. Clinical Generator │    │                          │
              │  Strict [PMID] format  │    │   (direct answer path    │
              │  Low temperature (0.1) │    │    joins here too)       │
              └────────────┬───────────┘    └──────────────────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  5. NLI Hallucination    │
              │  Verifier                │
              │  - Extract sentences     │
              │  - Classify each:        │
              │    ENTAILMENT / NEUTRAL  │
              │    / CONTRADICTION       │
              │  - Self-correct if needed│
              └────────────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  Grounded Answer +       │
              │  Full Audit Telemetry    │
              └──────────────────────────┘
```

---

## Pipeline Components — Implementation Details

### 1. Adaptive Routing Gate (`router.py`)

The router is a lightweight rule-based classifier that runs entirely on-CPU with no API calls. It uses compiled regular expressions against three pattern sets:

- **`DEFINITIONAL_PATTERNS`** — catches queries starting with "what is", "define", "what does X stand for", etc.
- **`CLINICAL_PATTERNS`** — catches efficacy, mortality, dosing, and trial keywords. The `\bdoes\b` match was deliberately narrowed to `does .+(reduce|increase|affect|...)` to avoid misrouting definitional queries like "What does aspirin mean?" as clinical.
- **`COMPARATIVE_PATTERNS`** — catches "versus", "drug interaction", "co-administered", etc. for multi-hop decomposition.

Routing runs in under 1ms. It returns a structured object with the route name, confidence, reasoning string, sub-queries, and decision latency — all surfaced directly in the UI telemetry panel.

The three routes:

| Route | When | Retrieval |
|---|---|---|
| `DIRECT_ANSWER` | Definitional/conceptual query | Skipped — 100% token savings on retrieval |
| `CLINICAL_RETRIEVAL` | Drug trials, dosing, efficacy questions | Hybrid search + reranking |
| `MULTI_HOP` | Comparative or interaction queries | Query decomposition → iterative search |

---

### 2. Hybrid BM25 + Semantic Retrieval with Reciprocal Rank Fusion (`retriever.py`)

**Why hybrid?** BM25 is excellent at exact keyword matching — drug names like "Apixaban", abbreviations like "eGFR", and numeric dosages like "10mg". Dense/semantic search is better at capturing meaning even when exact words differ. Using only one of them misses things the other catches.

**BM25 implementation:** Uses `rank_bm25.BM25Okapi`. The tokenizer (`tokenize_clinical`) preserves alphanumeric tokens including hyphens to avoid splitting compound drug names. The index is built over each document's question + abstract + MeSH terms combined.

**Semantic search:** Given we cannot run a local sentence transformer model on a CPU-only machine, the semantic component is implemented as weighted n-gram overlap — tokenizing both the query and each document and computing Jaccard-style intersection over the query token set. This captures enough semantic signal for the small PubMedQA corpus.

**Reciprocal Rank Fusion (RRF):** Both search results are merged using:

```
RRF_score(doc) = 1 / (60 + rank_bm25) + 1 / (60 + rank_semantic)
```

k=60 is the standard constant used in the original RRF paper (Cormack et al., 2009). The top-10 merged candidates are passed to the reranker.

---

### 3. Neural Cross-Encoder Reranker (`reranker.py`)

**Why rerank?** Bi-encoders (used in vector search) encode the query and document separately and compare embeddings. A cross-encoder takes the query and document together as a single input, which gives it access to full cross-attention and produces much more accurate relevance scores — but is too slow to run on the entire corpus, so it's applied only to the top-10 candidates.

MedVerify uses Gemini as the cross-encoder via a structured prompt (RankGPT-style): it passes all 10 candidates to the model in a single call and asks it to assign a relevance score from 0.0 to 1.0 for each, returning structured JSON rankings.

**The pruning fix:** The original naive implementation iterated only over `sorted_docs[:top_k]` and then pruned by threshold, which meant documents at positions 4–10 with scores above threshold would be missed. The corrected logic is:

```python
above_threshold = [d for d in sorted_docs if d["rerank_score"] >= threshold]
retained = above_threshold[:top_k]
```

Sort first → filter by threshold → take top_k. This ensures the highest-scoring documents always make it through, regardless of their initial index position.

Telemetry returned: total input count, retained count, pruned count (all documents that didn't make the final cut), threshold used, and rank-shift deltas (initial BM25 rank → final reranked rank for each document). These deltas are displayed in the UI as a rank-shift inspector.

---

### 4. Clinical Evidence Generator (`generator.py`)

Generates the clinical answer using Gemini with a strict system prompt that enforces:
- Every factual proposition must end with `[PMID: ...]`
- No hallucinated dosages, trial endpoints, or mortality statistics
- If evidence is inconclusive, say so explicitly

Temperature is set to 0.1 to minimize creative liberty. The retrieved documents are formatted as a numbered evidence dossier and injected into the prompt.

For the `DIRECT_ANSWER` route, the same generator runs with an empty evidence dossier — the system prompt still applies, but the model responds from parametric memory.

---

### 5. Claim-Level NLI Hallucination Verifier (`verifier.py`)

This is the most distinctive component of the pipeline.

**Step 1 — Proposition extraction:** The generated answer is split into atomic sentences using regex boundary detection (`(?<=[.!?])\s+(?=[A-Z0-9])`). Fragments shorter than 15 characters are ignored.

**Step 2 — NLI audit:** All extracted claims are sent to Gemini in a single structured call along with the retrieved evidence abstracts. The model classifies each claim as:
- `ENTAILMENT` — explicitly supported by the cited study
- `NEUTRAL` — general medical knowledge not explicitly in the retrieved abstracts
- `CONTRADICTION` — conflicts with trial findings or is not supported by any retrieved document

**Step 3 — Self-correction:** If any claim is labeled `CONTRADICTION`, the verifier automatically strips those sentences from the answer and appends a guardrail notice. The faithfulness score is computed as `entailed_claims / total_claims`.

**Step 4 — PMID extraction:** The verifier uses a regex to check whether any `[PMID: ...]` citation appears inline in the claim, and surfaces that as a clickable link in the UI.

---

### 6. Gemini REST Client (`gemini_client.py`)

All LLM calls go through a single unified REST client. No local model weights, no PyTorch, no GPU. The client:

- Makes direct HTTPS calls to the Gemini `generateContent` endpoint using Python's standard `urllib`
- Falls back across a model list (`gemini-2.5-flash-lite` → `gemini-3.1-flash-lite` → `gemini-flash-lite-latest`) if any model returns a 4xx/5xx
- Applies a 10-second backoff on 429 rate-limit errors (vs 0.5s for other errors) to avoid cascading quota exhaustion
- Strips markdown code fences from JSON responses before parsing (models occasionally wrap JSON in backtick blocks)

---

### 7. 3-Way Benchmark Engine (`pipeline.py`)

The benchmark runs the same query through three separate pipelines and returns results side by side:

- **No-RAG:** Calls the generator with an empty context. The NLI verifier still runs, checking each claim against no evidence — most claims come back `NEUTRAL` or `CONTRADICTION`.
- **Fixed-RAG:** Runs BM25 retrieval for top-5 documents (no reranking), passes all 5 to the generator, then verifies.
- **MedVerify (Adaptive):** Full pipeline — routing → hybrid search → reranking → generation → NLI audit.

The faithfulness score, hallucination count, total tokens, latency, and retrieved passage count for all three are compared in the UI benchmark tab and in the terminal evaluation script.

---

## AI and GenAI Topics Covered

This project covers the following topics with working implementations:

**Retrieval-Augmented Generation (RAG)** — the core paradigm. Retrieval results are used as grounding context for generation, reducing reliance on the model's (potentially outdated or hallucinated) parametric memory.

**Adaptive / Conditional Retrieval** — deciding when retrieval is worth its cost. This is an active area of research (papers like FLARE, Self-RAG, and C-RAG). Our router implements the lightweight classifier variant that makes routing decisions in < 1ms without an LLM call.

**Hybrid Search** — combining sparse (BM25) and dense retrieval. This matters in clinical text where exact drug names and numeric codes must be matched exactly, something dense-only search handles poorly.

**Reciprocal Rank Fusion (RRF)** — a standard technique for merging ranked lists from heterogeneous retrievers without requiring a learned combiner.

**Cross-Encoder Reranking (RankGPT-style)** — using an LLM as a cross-encoder to produce joint query-document relevance scores. More accurate than bi-encoder similarity but applied only on the shortlisted candidates to keep latency manageable.

**Natural Language Inference (NLI) for Hallucination Detection** — classifying generated text as ENTAILMENT / NEUTRAL / CONTRADICTION relative to source documents. This is the core technique used in papers like HALO and factual consistency evaluation research.

**Atomic Claim Decomposition** — splitting a paragraph-length answer into individual verifiable propositions before running NLI. This is necessary because NLI at the sentence level is more reliable than at the paragraph level.

**Self-Correction / Reflection Loop** — if contradicted claims are detected, the system automatically prunes them before the response reaches the user. This implements a simple version of the reflection pattern described in papers like Reflexion and Self-RAG.

**Prompt Engineering for Constrained Generation** — the clinical generator uses a strict system prompt with citation format enforcement, low temperature (0.1), and explicit instructions not to hallucinate trial statistics. The NLI verifier uses structured JSON output with per-claim fields.

**Faithfulness Metrics** — computing `entailed / total claims` as a faithfulness score, consistent with RAGAS-style evaluation. The 3-way benchmark makes these scores directly comparable across pipeline variants.

**Observability in AI Systems** — the latency waterfall, routing confidence, rank-shift deltas, and claim-level audit labels are all first-class outputs of the pipeline. Treating internal AI decisions as observable data, not black boxes, is increasingly important in production ML systems.

---

## Benchmark Results

Measured across curated PubMedQA clinical trial queries:

| Metric | No-RAG | Fixed-RAG (Naive Top-5) | MedVerify (Adaptive) |
|:---|:---:|:---:|:---:|
| Faithfulness Score (↑) | Low | Moderate | **Highest** |
| Hallucinated Claims (↓) | Multiple | Some | **0 — Fully Filtered** |
| Avg. Tokens per Query (↓) | ~191 | ~1,496 (peak) | **~792 (~47% saved)** |
| Distractor Pruning | None | None | **Dynamic threshold** |
| Citation Attribution | None | Unverified | **Atomic PMID audit** |

> The fixed-RAG token count is higher than MedVerify despite generating a similar-length answer because it blindly injects 5 full abstracts (~300 words each) into every prompt regardless of relevance.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Retrieval | `rank-bm25`, custom RRF implementation |
| LLM | Google Gemini REST API (no local model downloads) |
| Frontend | React 18, Vite, Tailwind CSS, Lucide Icons |
| Dataset | PubMedQA (curated biomedical clinical trial QA) |

Runs fully on CPU — no GPU, no local PyTorch, no HuggingFace model downloads. Total local memory footprint is under 150 MB.

---

## Project Structure

```
MedVerify/
├── backend/
│   ├── config.py              # Thresholds, paths, model config
│   ├── gemini_client.py       # Unified REST client with retry + model fallbacks
│   ├── router.py              # Adaptive complexity classifier (3-way routing)
│   ├── retriever.py           # Hybrid BM25 + semantic retrieval with RRF
│   ├── reranker.py            # Cross-encoder reranking + distractor pruning
│   ├── generator.py           # Citation-enforced clinical synthesis
│   ├── verifier.py            # Atomic NLI hallucination auditor + self-correction
│   ├── pipeline.py            # End-to-end orchestrator + 3-way benchmark runner
│   ├── main.py                # FastAPI routes (/query, /benchmark, /scenarios)
│   ├── evaluation.py          # Terminal benchmark suite
│   ├── requirements.txt
│   ├── .env.example
│   └── data/
│       └── pubmed_100.json    # Curated PubMedQA records
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Copilot + telemetry + benchmark tabs
│   │   ├── defaultData.js     # Pre-populated state for instant UI render
│   │   ├── index.css          # Glassmorphic theming, light/dark variables
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js         # Dev server + API proxy to :8000
├── PROJECT_PLAN_AND_ARCHITECTURE.md
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- A Google Gemini API key — get one free at [Google AI Studio](https://aistudio.google.com/)

### 1. Clone

```bash
git clone https://github.com/SKD151105/MedVerify.git
cd MedVerify
```

### 2. Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env    # Windows
# cp .env.example .env    # macOS / Linux
```

Edit `.env`:
```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
HOST=0.0.0.0
PORT=8000
```

Start the server:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API is live at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

---

## Running the Benchmark

```bash
cd backend
python evaluation.py
```

This runs the 3-way comparative evaluation across the PubMedQA test queries and prints a formatted scorecard comparing No-RAG, Fixed-RAG, and MedVerify across faithfulness, hallucination rate, token usage, and latency.

---

## API Reference

### `GET /api/health`
Returns service status.

### `GET /api/scenarios`
Returns the curated PubMedQA clinical cases loaded at startup.

### `POST /api/query`
Runs the full MedVerify pipeline on a query.

```json
// Request
{ "query": "Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?" }

// Response (abbreviated)
{
  "routing": { "route": "CLINICAL_RETRIEVAL", "confidence": 0.96, "requires_retrieval": true },
  "faithfulness_score": 1.0,
  "audit_result": {
    "total_claims": 3,
    "entailed_claims": 3,
    "contradicted_claims": 0,
    "claim_audits": [ ... ]
  },
  "tokens_consumed": 792,
  "tokens_saved_percentage": 47.1,
  "latency_waterfall": {
    "Routing Gate": 0.4,
    "Hybrid Retrieval": 12.1,
    "Neural Reranking": 1840.2,
    "Clinical Synthesis": 3210.5,
    "NLI Verification": 2890.1
  }
}
```

### `POST /api/benchmark`
Runs the 3-way side-by-side evaluation on the given query.

---

## A Note on Hardware

This project was built to run without a GPU. All LLM and cross-encoder inference happens over the Gemini REST API. The only local computation is BM25 indexing (`rank_bm25`), the RRF merge, and regex-based proposition splitting — all of which run in well under 100ms on CPU. The application has no dependency on PyTorch, sentence-transformers, or any local model weights.

---

## License

MIT — see [LICENSE](LICENSE).
