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

**BM25 Lexical Model:** Uses Okapi BM25 scoring over clinical trial questions, abstracts, and MeSH terms:

$$
\text{Score}_{\text{BM25}}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}
$$

$$
\text{IDF}(q_i) = \ln \left( \frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1 \right)
$$

where:
- $f(q_i, D)$ is the term frequency of token $q_i$ in document $D$.
- $|D|$ and $\text{avgdl}$ represent document length and average document length across the corpus.
- $k_1 = 1.5$ (term frequency saturation) and $b = 0.75$ (document length penalization).

The tokenizer (`tokenize_clinical`) preserves alphanumeric tokens including hyphens to avoid splitting compound drug names (e.g., `stages 1 to 3b`, `eGFR`).

**Reciprocal Rank Fusion (RRF):** Both sparse lexical hits and semantic overlap ranks are merged into a single ranked pool without requiring manual score calibration:

$$
\text{RRF}_{\text{Score}}(d) = \sum_{m \in \{\text{BM25}, \text{Semantic}\}} \frac{1}{k + r_m(d)}
$$

where $r_m(d) \in [1, 20]$ is the rank of document $d$ in retriever $m$, and $k = 60$ is the standard smoothing parameter (Cormack et al., 2009). The top-10 merged candidates are forwarded to the neural reranker.

---

### 3. Neural Cross-Encoder Reranker (`reranker.py`)

**Why rerank?** Bi-encoders encode query and document separately into static vectors. A cross-encoder takes the query and document together as a joint input, granting full cross-attention over the query-passage interaction:

$$
s_{\text{cross}}(q, d) = P(\text{Relevant} \mid q, d) \in [0.0, 1.0]
$$

MedVerify uses Gemini as the cross-encoder via a structured prompt (RankGPT-style): it evaluates candidate abstracts in a single structured call and outputs a joint relevance score $s_{\text{cross}}(q, d) \in [0.0, 1.0]$.

**Dynamic Distractor Pruning:** Documents scoring below the clinical relevance cutoff $\tau = 0.25$ are discarded as distractors before passage selection:

$$
\mathcal{D}_{\text{retained}} = \text{Top-}k \Big(\{ d \in \mathcal{D}_{\text{candidates}} \mid s_{\text{cross}}(q, d) \ge \tau \}\Big)
$$

where $k = 3$. Candidates are sorted descending by $s_{\text{cross}}$ and filtered before slicing top-$k$, ensuring high-scoring papers are never dropped due to arbitrary index boundaries.

**Rank-Shift Delta Metric:** For observability, the shift between initial retrieval rank $r_{\text{initial}}(d)$ and reranked position $r_{\text{reranked}}(d)$ is measured:

$$
\Delta_{\text{rank}}(d) = r_{\text{initial}}(d) - r_{\text{reranked}}(d)
$$

A positive delta ($\Delta_{\text{rank}} > 0$) indicates promotion by joint cross-attention, surfacing clinical trials that naive keyword/bi-encoder search ranked poorly.

---

### 4. Clinical Evidence Generator (`generator.py`)

Generates the clinical answer using Gemini with a strict system prompt that enforces:
- Every factual proposition must end with `[PMID: ...]`
- No hallucinated dosages, trial endpoints, or mortality statistics
- If evidence is inconclusive, say so explicitly

Temperature is set to 0.1 to minimize creative liberty. The retrieved documents are formatted as a numbered evidence dossier and injected into the prompt.

For the `DIRECT_ANSWER` route, the same generator runs with an empty evidence dossier — the system prompt still applies, but the model responds from parametric memory without fabricating citations.

---

### 5. Claim-Level NLI Hallucination Verifier (`verifier.py`)

This is the primary factual guardrail of the pipeline.

**Step 1 — Proposition Extraction:** The generated answer $A$ is segmented into $n$ atomic factual sentences using syntactic regex boundary detection:

$$
\mathcal{C}_A = \{c_1, c_2, \dots, c_n\}
$$

**Step 2 — NLI Premise-Hypothesis Audit:** Each proposition $c_i$ is evaluated against the retrieved evidence dossier $\mathcal{E}$ via Natural Language Inference:

$$
\text{NLI}(c_i, \mathcal{E}) \in \{\text{ENTAILMENT}, \text{NEUTRAL}, \text{CONTRADICTION}\}
$$

- `ENTAILMENT`: The assertion is mathematically or factually supported by the premise abstract.
- `NEUTRAL`: General medical knowledge not stated in the retrieved context.
- `CONTRADICTION`: Conflicts with the trial findings or asserts fabricated statistics.

**Step 3 — Phantom Citation Detection:** Every cited PMID is cross-referenced against the valid PMIDs present in the retrieved evidence set:

$$
\mathcal{P}_{\text{retrieved}} = \{\text{PMID}(d) \mid d \in \mathcal{E}\}
$$

$$
\text{PhantomCitation}(c_i) = \mathbb{I}\Big(\text{CitedPMID}(c_i) \neq \emptyset \land \text{CitedPMID}(c_i) \notin \mathcal{P}_{\text{retrieved}}\Big)
$$

If $\text{PhantomCitation}(c_i) = 1$, the claim is automatically classified as `CONTRADICTION`.

**Step 4 — Faithfulness Score Calculation:**

$$
\text{Faithfulness}(A, \mathcal{E}) = \frac{1}{n} \sum_{i=1}^{n} \mathbb{I}\Big(\text{NLI}(c_i, \mathcal{E}) = \text{ENTAILMENT}\Big)
$$

where $n$ is the total claim count. For parametric baseline queries with no external evidence ($\mathcal{E} = \emptyset$, No-RAG), $\text{Faithfulness} = 0.0$.

**Step 5 — Self-Correction Protocol:** If any claim is labeled `CONTRADICTION`, the verifier automatically strips the unverified assertion and appends an auditable guardrail notice to prevent clinical misinformation from reaching the clinician.

---

### 6. Gemini REST Client (`gemini_client.py`)

All LLM calls go through a single unified REST client. No local model weights, no PyTorch, no GPU. The client:

- Makes direct HTTPS calls to the Gemini `generateContent` endpoint using Python's standard `urllib`
- Configures `responseMimeType: "application/json"` with automatic LaTeX backslash sanitization (`re.sub`) to prevent `Invalid \escape` JSONDecodeErrors
- Falls back across active fast models (`gemini-3-flash-preview` → `gemini-3.5-flash-lite` → `gemini-flash-lite-latest`)
- Applies exponential backoff on HTTP 429 rate-limit responses
- Operates with a 25-second connection timeout, eliminating thread stalls

---

### 7. 3-Way Benchmark Engine (`pipeline.py`)

The benchmark evaluates the exact same clinical query across three paradigms concurrently via `concurrent.futures.ThreadPoolExecutor`:

1. **No-RAG (Parametric LLM):** Evaluates generator outputs with $\mathcal{E} = \emptyset$. Since zero external documents exist, logical entailment is zero (Faithfulness = 0.0%), and any hallucinated citations are flagged.
2. **Fixed-RAG (Naive Blind Top-5):** Injects all top-5 candidates directly into the prompt without reranking or distractor filtering.
3. **MedVerify (Adaptive Pipeline):** Executes the full routing $\to$ hybrid search $\to$ cross-encoder rerank $\to$ NLI audit flow.

**Token Consumption & Efficiency Formulation:**
For Fixed-RAG:

$$
T_{\text{Fixed-RAG}} = T_{\text{overhead}} + \sum_{i=1}^{5} \text{Tokens}(d_i) + T_{\text{completion}}
$$

For MedVerify:

$$
T_{\text{MedVerify}} = T_{\text{overhead}} + \sum_{d \in \mathcal{D}_{\text{retained}}} \text{Tokens}(d) + T_{\text{completion}}
$$

The **Tokens Saved Percentage** is computed from empirical usage metadata:

$$
\text{Tokens Saved \%} = \max\left(0, \frac{T_{\text{Fixed-RAG}} - T_{\text{MedVerify}}}{T_{\text{Fixed-RAG}}}\right) \times 100
$$

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

## Mathematical Formulations & Formal Specifications

MedVerify unifies several mathematical formulations across information retrieval, natural language inference, and cost optimization:

### 1. Lexical Scoring (Okapi BM25)

$$
\text{Score}_{\text{BM25}}(D, Q) = \sum_{i=1}^{n} \ln\left(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1\right) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}
$$

Where:
- $k_1 = 1.5$ (term frequency saturation)
- $b = 0.75$ (document length penalization)
- $N$ is the total corpus size
- $n(q_i)$ is the document frequency of query token $q_i$

### 2. Reciprocal Rank Fusion (RRF)

$$
\text{RRF}(d) = \sum_{m \in \{\text{BM25}, \text{Semantic}\}} \frac{1}{k + r_m(d)}
$$

Where rank smoothing constant $k = 60$. RRF merges heterogeneous sparse and dense rankings into a unified candidate pool without requiring score normalization.

### 3. Dynamic Cross-Encoder Pruning & Rank Shift

$$
s_{\text{cross}}(q, d) = P(\text{Relevant} \mid q, d) \in [0.0, 1.0]
$$

$$
\mathcal{D}_{\text{retained}} = \text{Top-}k \Big(\{ d \in \mathcal{D}_{\text{candidates}} \mid s_{\text{cross}}(q, d) \ge \tau \}\Big)
$$

$$
\Delta_{\text{rank}}(d) = r_{\text{initial}}(d) - r_{\text{reranked}}(d)
$$

Where pruning threshold $\tau = 0.25$ and candidate budget $k = 3$. A positive rank shift ($\Delta_{\text{rank}} > 0$) indicates promotion by joint cross-attention over naive lexical search.

### 4. Claim Decomposition & Faithfulness Score

Let $A$ be decomposed into $n$ atomic declarative claims:

$$
\mathcal{C}_A = \{c_1, c_2, \dots, c_n\}
$$

Given retrieved evidence context $\mathcal{E}$, Faithfulness is computed as the proportion of entailed claims:

$$
\text{Faithfulness}(A, \mathcal{E}) = \frac{1}{n} \sum_{i=1}^{n} \mathbb{I}\Big(\text{NLI}(c_i, \mathcal{E}) = \text{ENTAILMENT}\Big)
$$

For parametric baseline evaluation without retrieved evidence ($\mathcal{E} = \emptyset$, No-RAG), $\text{Faithfulness} = 0.0$.

### 5. Phantom Citation & Hallucination Rate

Let the set of valid PMIDs present in the retrieved evidence dossier be:

$$
\mathcal{P}_{\text{retrieved}} = \{\text{PMID}(d) \mid d \in \mathcal{E}\}
$$

A cited PMID in claim $c_i$ is classified as a phantom citation if it does not originate from $\mathcal{P}_{\text{retrieved}}$:

$$
\text{PhantomCitation}(c_i) = \mathbb{I}\Big(\text{CitedPMID}(c_i) \neq \emptyset \land \text{CitedPMID}(c_i) \notin \mathcal{P}_{\text{retrieved}}\Big)
$$

$$
\text{Hallucination Count} = \sum_{i=1}^{n} \mathbb{I}\Big(\text{NLI}(c_i, \mathcal{E}) = \text{CONTRADICTION} \lor \text{PhantomCitation}(c_i) = 1\Big)
$$

### 6. Token Savings Percentage

$$
T_{\text{Fixed-RAG}} = T_{\text{overhead}} + \sum_{i=1}^{5} \text{Tokens}(d_i) + T_{\text{completion}}
$$

$$
T_{\text{MedVerify}} = T_{\text{overhead}} + \sum_{d \in \mathcal{D}_{\text{retained}}} \text{Tokens}(d) + T_{\text{completion}}
$$

$$
\text{Tokens Saved \%} = \max\left(0, \frac{T_{\text{Fixed-RAG}} - T_{\text{MedVerify}}}{T_{\text{Fixed-RAG}}}\right) \times 100
$$

---

## Empirical Benchmark Results

Measured across PubMedQA clinical trial queries comparing the three paradigms side by side:

| Metric | No-RAG (Parametric) | Fixed-RAG (Naive Top-5) | MedVerify (Adaptive) |
|:---|:---:|:---:|:---:|
| **Faithfulness Score (↑)** | **0.0%** *(Zero evidence)* | **67.0%** *(Distractor noise)* | **100.0%** *(Fully Entailed)* 🏆 |
| **Hallucinated Claims Flagged (↓)** | **3** *(Phantom citations)* | **2** *(Distractor claims)* | **0** *(Guardrail Filtered)* 🛡️ |
| **Tokens Consumed per Query (↓)** | 398 | 1,408 *(Highest)* | **895** *(**36.4% Saved**)* 💰 |
| **Distractor Pruning** | N/A | None (All 5 stuffed) | **Dynamic Threshold ($\tau = 0.25$)** |
| **Claim-Level Grounding** | None | Unverified | **Atomic NLI Entailment Audit** |
| **Average Benchmark Latency** | ~6.2s | ~14.1s | **~5.8s** *(Optimized)* |

> **Key Takeaways:**
> 1. **No-RAG** fails completely on clinical trials because parametric memory fabricates phantom PMIDs and produces ungrounded assertions (Faithfulness = 0.0%).
> 2. **Fixed-RAG** achieves moderate faithfulness (67%) but burns **1,408 tokens** by stuffing irrelevant distractors (e.g., COVID or surgical statin papers into a nephrology query).
> 3. **MedVerify** maintains **100% faithfulness** while cutting token overhead by **36.4%** via cross-encoder pruning and automated self-correction.

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
