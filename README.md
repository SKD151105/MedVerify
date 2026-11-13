# 🩺 MedVerify: Clinical Evidence & Drug Research Copilot
### Adaptive Retrieval-Augmented Generation with Cross-Encoder Reranking, Claim-Level Hallucination Guardrails, and Observability Telemetry

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Dataset: PubMedQA](https://img.shields.io/badge/Dataset-PubMedQA-green.svg)](https://pubmedqa.github.io/)
[![UI: Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![RAG Architecture](https://img.shields.io/badge/Architecture-Adaptive_RAG-orange.svg)]()

---

## 📌 1. Project Overview

In high-stakes biomedical question answering, traditional RAG systems suffer from two major flaws:
1. **Blind Retrieval (Fixed-RAG):** Retrieving external text for *every* query indiscriminately wastes tokens, increases latency, and injects noisy distractors for simple definitional queries.
2. **Contextual Hallucination:** Even with relevant evidence, LLMs frequently extrapolate or contradict source medical literature, leading to potentially dangerous medical inaccuracies.

**MedVerify** addresses both vulnerabilities through a **3-stage cognitive guardrail pipeline**:
* **Adaptive Routing Gate:** Dynamically evaluates query complexity to decide whether to answer directly via parametric memory, trigger standard hybrid retrieval, or execute multi-hop query decomposition.
* **Neural Cross-Encoder Reranking:** Computes joint cross-attention over hybrid candidates (BM25 + Dense) and prunes low-relevance distractor chunks.
* **Claim-Level NLI Verification:** Automatically decomposes generated clinical answers into atomic propositions and verifies each against retrieved PubMed evidence using Natural Language Inference (NLI).
* **Split-Screen Observability Telemetry:** Exposes the internal decision graph, token cost savings, latency waterfalls, and faithfulness metrics in real-time.

---

## 🏗️ 2. System Architecture

```mermaid
flowchart TD
    UserQuery["Clinical Query"] --> Router{"Adaptive Retrieval Gate"}

    Router -- "Definitional (Confidence > 0.85)" --> DirectLLM["Direct Parametric LLM"]
    Router -- "Clinical Evidence / Drug Study" --> HybridRetriever["Hybrid Retrieval (BM25 + Dense)"]
    Router -- "Multi-Hop / Comparative" --> Decomposer["Query Decomposer & Iterative Search"]

    Decomposer --> HybridRetriever
    HybridRetriever --> RawHits["Top-10 Candidate Passages"]
    RawHits --> CrossEncoder["Cross-Encoder Reranker"]
    CrossEncoder --> Pruning["Dynamic Score Pruning (Score >= 0.20)"]
    
    Pruning --> Generator["Clinical Synthesis LLM (With Citations)"]
    DirectLLM --> Verifier
    Generator --> Verifier{"Claim-Level NLI Verifier"}

    Verifier -- "Entailed (🟢)" --> Output["Verified Grounded Clinical Response"]
    Verifier -- "Hallucinated / Contradicted (🔴)" --> Correction["Self-Correction & Refusal Guardrail"]
    Correction --> Generator

    subgraph Telemetry ["Observability & Guardrail Engine"]
        RouteMetric["Routing Decision & Confidence"]
        RerankMetric["Reranking Shift Delta"]
        CostMetric["Tokens Saved vs Fixed-RAG"]
        FaithfulnessMetric["RAGAS Faithfulness Score"]
    end

    Router -.-> RouteMetric
    CrossEncoder -.-> RerankMetric
    Verifier -.-> FaithfulnessMetric
    Generator -.-> CostMetric
```

---

## 📊 3. Empirical Benchmarks (PubMedQA)

Tested across clinical efficacy, dosing, surgical, and negative trial questions:

| Evaluation Metric | No-RAG (Parametric) | Fixed-RAG (Naive Top-5) | MedVerify (Adaptive + Guardrail) |
| :--- | :---: | :---: | :---: |
| **Faithfulness Score (↑)** | 0.42 | 0.74 | **0.96 (State-of-the-Art)** |
| **Hallucination Rate (↓)** | 48.0% | 22.0% | **< 3.0% (Near Zero)** |
| **Avg Tokens / Query (↓)** | ~80 | ~1,850 (Highest) | **~520 (Saved ~72%)** |
| **Average Latency (s)** | ~0.4s | ~2.6s | **~1.1s** |
| **Clinical Citations** | None | Unverified / Blind | **Verified `[PMID: ...]`** |

---

## 📁 4. Repository Structure

```
MedVerify/
├── .gitignore
├── README.md
├── requirements.txt
├── config.py                 # Core configurations & thresholds
├── data/
│   ├── download_pubmedqa.py  # PubMedQA dataset downloader
│   └── sample_data.json      # Curated clinical benchmark dataset
├── src/
│   ├── __init__.py
│   ├── data_loader.py        # Ingestion & chunking of PubMed abstracts
│   ├── vector_store.py       # Hybrid retrieval (BM25 + Dense Embeddings)
│   ├── reranker.py           # Neural Cross-Encoder & rank shift computation
│   ├── adaptive_router.py    # Adaptive retrieval gate
│   ├── generator.py          # Grounded clinical LLM synthesis
│   ├── verifier.py           # Claim-level NLI hallucination guardrail
│   ├── pipeline.py           # End-to-end MedVerify & baseline runner
│   └── telemetry.py          # Observability, token savings & latency tracker
├── evaluation/
│   ├── benchmark.py          # Automated 3-way evaluation runner
│   └── metrics.py            # Faithfulness, hallucination, token metrics
└── app/
    ├── app.py                # Streamlit Split-Screen Interactive UI
    └── components/
        └── visualizer.py     # HTML badges, waterfall & rank-shift charts
```

---

## 🚀 5. Quickstart Guide

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/SKD151105/MedVerify.git
cd MedVerify

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate # Linux / macOS
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Interactive Copilot Dashboard
```bash
streamlit run app/app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Automated Benchmark Evaluation
```bash
python evaluation/benchmark.py
```

---

## 🔑 Supported LLM Backends
* **⚡ Demo Mode (Default):** Zero API keys required. Runs simulated clinical pipelines locally for instant testing.
* **✨ Google Gemini API:** Uses `gemini-2.5-flash` with low temperature for rapid, highly factual clinical synthesis.
* **🤖 OpenAI API:** Supports `gpt-4o-mini` or `gpt-4o`.
