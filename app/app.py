"""
MedVerify: Clinical Evidence & Drug Research Copilot
Next-Generation Glassmorphic Streamlit Dashboard with Real-Time Observability.
"""

import sys
from pathlib import Path

# Add project root and app dir to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st
import pandas as pd
from src.pipeline import MedVerifyPipeline

try:
    from components.visualizer import (
        render_claim_highlighted_html,
        create_latency_waterfall_chart,
        create_rank_shift_chart
    )
except ImportError:
    from app.components.visualizer import (
        render_claim_highlighted_html,
        create_latency_waterfall_chart,
        create_rank_shift_chart
    )

st.set_page_config(
    page_title="MedVerify Copilot | Clinical Evidence & Guardrails",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Background and Layout Polish */
    .stApp {
        background: radial-gradient(circle at 10% 10%, rgba(14, 23, 42, 0.95), rgba(9, 13, 22, 1));
        color: #F1F5F9;
    }

    /* Hero Header */
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.3);
        color: #38BDF8;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        background: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10B981;
    }

    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #BAE6FD 50%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        margin-bottom: 4px;
    }

    .hero-subtitle {
        font-size: 0.98rem;
        color: #94A3B8;
        margin-bottom: 24px;
        line-height: 1.5;
    }

    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4);
        margin-bottom: 18px;
        backdrop-filter: blur(8px);
    }

    .glass-card:hover {
        border-color: rgba(56, 189, 248, 0.25);
        transition: all 0.2s ease-in-out;
    }

    /* Custom Metric Tiles */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 18px;
    }

    .metric-box {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 14px 16px;
        text-align: left;
    }

    .metric-box-title {
        font-size: 0.75rem;
        color: #94A3B8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }

    .metric-box-val {
        font-size: 1.45rem;
        font-weight: 700;
        color: #F8FAFC;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Evidence Box */
    .evidence-item {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }

    /* Tab Polish */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 600;
        color: #94A3B8;
        background: transparent;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.15) !important;
        color: #38BDF8 !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
    }

    /* Sidebar buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0284C7 0%, #2563EB 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
        transition: transform 0.1s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def get_pipeline(provider: str, api_key: str):
    return MedVerifyPipeline(llm_provider=provider, api_key=api_key)


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
        <span style="font-size: 2rem;">🩺</span>
        <div>
            <div style="font-weight: 700; font-size: 1.15rem; color: #FFFFFF;">MedVerify</div>
            <div style="font-size: 0.75rem; color: #38BDF8; font-weight: 500;">CLINICAL RAG WORKBENCH</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("##### ⚙️ LLM Runtime Configuration")
    provider = st.selectbox(
        "Engine Mode",
        ["mock", "gemini", "openai"],
        format_func=lambda x: {
            "mock": "⚡ Zero-Setup Demo (Local Mock)",
            "gemini": "✨ Google Gemini API (gemini-2.5-flash)",
            "openai": "🤖 OpenAI API (gpt-4o-mini)"
        }[x]
    )

    api_key = ""
    if provider in ["gemini", "openai"]:
        api_key = st.text_input(
            f"{provider.upper()} API Key",
            type="password",
            help="Your API key stays strictly in this local session."
        )

    st.divider()
    st.markdown("##### 🧪 Clinical Test Cases (PubMedQA)")

    sample_queries = [
        "Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?",
        "What is the recommended dose adjustment for Apixaban in patients with severe renal impairment?",
        "Do preoperative statins reduce the incidence of postoperative atrial fibrillation after coronary artery bypass grafting?",
        "Does routine hydroxychloroquine administration improve clinical recovery in hospitalized COVID-19 patients?",
        "What is essential hypertension?",
        "In a diabetic patient with eGFR of 35 mL/min and a history of atrial fibrillation, can Metformin and Apixaban be co-administered safely?"
    ]

    selected_sample = st.selectbox("Preset Question:", sample_queries)
    custom_query = st.text_area("Or input query:", value=selected_sample, height=85)

    execute_btn = st.button("🚀 Run Cognitive Pipeline", use_container_width=True)

    st.markdown("""
    <div style="font-size: 0.76rem; color: #64748B; margin-top: 20px; line-height: 1.4;">
        <strong>Datasets:</strong> PubMedQA (Expert-labeled)<br>
        <strong>Reranker:</strong> Cross-Encoder MiniLM<br>
        <strong>Verifier:</strong> NLI DeBERTa Proposition Engine
    </div>
    """, unsafe_allow_html=True)


# --- HERO HEADER ---
st.markdown("""
<div class="hero-badge">
    <div class="pulse-dot"></div>
    Adaptive Guardrail System Active
</div>
<div class="hero-title">MedVerify Clinical Copilot</div>
<div class="hero-subtitle">
    Evidence-grounded clinical decision support with dynamic retrieval gating, cross-encoder neural reranking, and proposition-level hallucination verification.
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "📊 Live Copilot & Observability",
    "🔬 3-Way Baseline Benchmark (No-RAG vs Fixed vs MedVerify)",
    "📖 Architecture & Research Specification"
])

# Initialize Pipeline
with st.spinner("Initializing MedVerify Hybrid Engine & Vector Index..."):
    pipeline = get_pipeline(provider=provider, api_key=api_key)

if "analysis_result" not in st.session_state or execute_btn:
    query_to_run = custom_query if custom_query.strip() else selected_sample
    with st.spinner("Executing: Routing Gate ➔ Hybrid Retrieval ➔ Neural Rerank ➔ Clinical Synthesis ➔ NLI Verification..."):
        st.session_state.analysis_result = pipeline.run_adaptive_pipeline(query_to_run)
        st.session_state.benchmark_result = pipeline.run_baseline_comparison(query_to_run)

res = st.session_state.analysis_result
bench = st.session_state.benchmark_result


# --- TAB 1: COPILOT VIEW ---
with tab1:
    # Top KPI Metrics Row
    route_name = res["routing"]["route"].replace("_", " ")
    faith_pct = int(res["audit_result"]["faithfulness_score"] * 100)
    saved_pct = res["cost_savings"]["percentage_tokens_saved"]
    latency_sec = res["total_execution_time_s"]

    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-box">
            <div class="metric-box-title">Adaptive Route</div>
            <div class="metric-box-val" style="color: #38BDF8;">{route_name}</div>
        </div>
        <div class="metric-box">
            <div class="metric-box-title">Faithfulness Score</div>
            <div class="metric-box-val" style="color: {'#34D399' if faith_pct >= 80 else '#FBBF24'};">{faith_pct}%</div>
        </div>
        <div class="metric-box">
            <div class="metric-box-title">Tokens Saved vs Fixed</div>
            <div class="metric-box-val" style="color: #A78BFA;">{saved_pct}%</div>
        </div>
        <div class="metric-box">
            <div class="metric-box-title">Total Latency</div>
            <div class="metric-box-val" style="color: #F8FAFC;">{latency_sec}s</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1.15, 0.85], gap="large")

    # LEFT COLUMN: Doctor's Clinical View
    with col_left:
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 1.1rem; color: #FFFFFF;">📋 Clinical Synthesis</span>
            <span style="font-size: 0.75rem; color: #94A3B8;">Proposition-Level Verification</span>
        </div>
        """, unsafe_allow_html=True)

        highlighted_html = render_claim_highlighted_html(res["audit_result"]["claim_audits"])
        st.markdown(f"""
        <div class="glass-card" style="border-left: 4px solid #38BDF8;">
            <div style="font-size: 0.82rem; color: #94A3B8; margin-bottom: 12px; font-weight: 600;">
                QUERY: <span style="color: #F1F5F9;">{res['query']}</span>
            </div>
            {highlighted_html}
        </div>
        """, unsafe_allow_html=True)

        if res["audit_result"]["has_hallucination"]:
            st.error("🛡️ **Guardrail Intervention:** MedVerify identified ungrounded or contradicted claims in the preliminary synthesis and applied self-correction.")

        # Evidence Dossier
        with st.expander(f"📚 Cited PubMed Evidence Dossier ({len(res['reranked_docs'])} studies retained)", expanded=True):
            if res["reranked_docs"]:
                for i, doc in enumerate(res["reranked_docs"], start=1):
                    delta = doc.get("rank_delta", 0)
                    delta_color = "#34D399" if delta > 0 else ("#FB7185" if delta < 0 else "#94A3B8")
                    delta_str = f"+{delta}" if delta > 0 else f"{delta}"

                    st.markdown(f"""
                    <div class="evidence-item">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 700; color: #38BDF8; font-size: 0.92rem;">
                                Reference [{i}] • PMID {doc['pmid']}
                            </span>
                            <span style="font-size: 0.75rem; background: rgba(255,255,255,0.06); padding: 3px 8px; border-radius: 4px; font-family: monospace;">
                                Rerank Score: <strong>{doc.get('raw_rerank_score', 0):.3f}</strong> 
                                (<span style="color: {delta_color}; font-weight: 600;">Rank {delta_str}</span>)
                            </span>
                        </div>
                        <div style="font-size: 0.88rem; font-weight: 600; color: #E2E8F0; margin-bottom: 6px;">
                            {doc['question']}
                        </div>
                        <div style="font-size: 0.82rem; color: #94A3B8; line-height: 1.55; white-space: pre-line;">
                            {doc['content'][:360]}...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ No external literature retrieved: Query was answered directly through parametric memory (Definitional Route).")

    # RIGHT COLUMN: Observability Telemetry
    with col_right:
        st.markdown('<div style="font-weight: 700; font-size: 1.1rem; color: #FFFFFF; margin-bottom: 8px;">🛡️ Real-Time Observability</div>', unsafe_allow_html=True)

        # 1. Routing Card
        r_info = res["routing"]
        st.markdown(f"""
        <div class="glass-card" style="padding: 14px 16px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.8rem; font-weight: 700; color: #38BDF8; text-transform: uppercase;">1. Adaptive Routing Gate</span>
                <span style="font-size: 0.75rem; color: #94A3B8; font-family: monospace;">{r_info['decision_latency_ms']} ms</span>
            </div>
            <div style="font-size: 0.84rem; color: #CBD5E1; margin-bottom: 8px;">
                {r_info['reasoning']}
            </div>
            <div style="font-size: 0.78rem; color: #94A3B8; margin-bottom: 4px;">Gate Confidence: <strong>{int(r_info['confidence']*100)}%</strong></div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Reranking Chart
        st.markdown("""
        <div class="glass-card" style="padding: 14px 16px; margin-bottom: 14px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #A78BFA; text-transform: uppercase; margin-bottom: 8px;">
                2. Cross-Encoder Rank-Shift Delta
            </div>
        """, unsafe_allow_html=True)
        if res["rerank_telemetry"].get("rank_shifts"):
            fig_rerank = create_rank_shift_chart(res["rerank_telemetry"]["rank_shifts"])
            st.plotly_chart(fig_rerank, use_container_width=True)
            st.caption(f"Retained top {res['rerank_telemetry']['candidates_retained']} chunks; dropped {res['rerank_telemetry']['candidates_pruned']} low-scoring distractor abstracts.")
        else:
            st.caption("Direct Answer route active. Cross-Encoder bypassed to save computation.")
        st.markdown("</div>", unsafe_allow_html=True)

        # 3. Latency Waterfall Chart
        st.markdown("""
        <div class="glass-card" style="padding: 14px 16px; margin-bottom: 14px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #34D399; text-transform: uppercase; margin-bottom: 8px;">
                3. End-to-End Latency Breakdown
            </div>
        """, unsafe_allow_html=True)
        fig_waterfall = create_latency_waterfall_chart(res["latency_waterfall"])
        st.plotly_chart(fig_waterfall, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 4. Proposition Audit Table
        with st.expander("📋 Proposition Audit Table (NLI Scores)"):
            audit_df = pd.DataFrame(res["audit_result"]["claim_audits"])[["claim", "label", "confidence", "cited_pmid"]]
            st.dataframe(audit_df, use_container_width=True)


# --- TAB 2: BASELINE BENCHMARK ---
with tab2:
    st.markdown("### 🔬 3-Way Comparative Benchmark on Current Query")
    st.caption("Quantitative comparison of **No-RAG**, **Naive Fixed-RAG**, and **MedVerify**.")

    b_no = bench["no_rag"]
    b_fix = bench["fixed_rag"]
    b_med = bench["medverify"]

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown(f"""
        <div class="glass-card" style="border-top: 3px solid #64748B;">
            <div style="font-weight: 700; font-size: 1rem; color: #94A3B8; margin-bottom: 12px;">1️⃣ No-RAG (Parametric)</div>
            <div style="font-size: 0.85rem; line-height: 2;">
                <div>Faithfulness: <strong style="color: #FB7185;">{int(b_no['faithfulness']*100)}%</strong></div>
                <div>Hallucinated Claims: <strong>{b_no['hallucinations_detected']}</strong></div>
                <div>Tokens Consumed: <strong>{b_no['total_tokens']}</strong></div>
                <div>End-to-End Latency: <strong>{b_no['latency_s']}s</strong></div>
                <div>Retrieved Passages: <strong>0</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("View Output"):
            st.caption(b_no["answer"])

    with col2:
        st.markdown(f"""
        <div class="glass-card" style="border-top: 3px solid #F59E0B;">
            <div style="font-weight: 700; font-size: 1rem; color: #FBBF24; margin-bottom: 12px;">2️⃣ Fixed-RAG (Naive Top-5)</div>
            <div style="font-size: 0.85rem; line-height: 2;">
                <div>Faithfulness: <strong style="color: #FBBF24;">{int(b_fix['faithfulness']*100)}%</strong></div>
                <div>Hallucinated Claims: <strong>{b_fix['hallucinations_detected']}</strong></div>
                <div>Tokens Consumed: <strong style="color: #FB7185;">{b_fix['total_tokens']} (Highest)</strong></div>
                <div>End-to-End Latency: <strong>{b_fix['latency_s']}s</strong></div>
                <div>Retrieved Passages: <strong>{b_fix['retrieved_docs_count']} (Blind)</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("View Output"):
            st.caption(b_fix["answer"])

    with col3:
        st.markdown(f"""
        <div class="glass-card" style="border-top: 3px solid #38BDF8;">
            <div style="font-weight: 700; font-size: 1rem; color: #38BDF8; margin-bottom: 12px;">3️⃣ MedVerify (Adaptive + Guardrail) 🏆</div>
            <div style="font-size: 0.85rem; line-height: 2;">
                <div>Faithfulness: <strong style="color: #34D399;">{int(b_med['faithfulness']*100)}% (Highest)</strong></div>
                <div>Hallucinated Claims: <strong style="color: #34D399;">{b_med['hallucinations_detected']} (Protected)</strong></div>
                <div>Tokens Consumed: <strong style="color: #38BDF8;">{b_med['total_tokens']} (Saved {b_med['tokens_saved_pct']}%)</strong></div>
                <div>End-to-End Latency: <strong>{b_med['latency_s']}s</strong></div>
                <div>Retrieved Passages: <strong>{b_med['retrieved_docs_count']} (Pruned)</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("View Output"):
            st.caption(b_med["answer"])

    st.markdown("#### 📊 Consolidated Metric Scorecard")
    comparison_data = {
        "Metric": ["Faithfulness Score", "Hallucinated Claims", "Tokens Consumed", "Latency (s)", "Retrieved Passages"],
        "No-RAG": [f"{int(b_no['faithfulness']*100)}%", b_no["hallucinations_detected"], b_no["total_tokens"], f"{b_no['latency_s']}s", b_no["retrieved_docs_count"]],
        "Fixed-RAG (Naive)": [f"{int(b_fix['faithfulness']*100)}%", b_fix["hallucinations_detected"], b_fix["total_tokens"], f"{b_fix['latency_s']}s", b_fix["retrieved_docs_count"]],
        "MedVerify (Adaptive)": [f"{int(b_med['faithfulness']*100)}%", b_med["hallucinations_detected"], b_med["total_tokens"], f"{b_med['latency_s']}s", b_med["retrieved_docs_count"]]
    }
    st.table(pd.DataFrame(comparison_data))


# --- TAB 3: TECHNICAL SPEC ---
with tab3:
    st.markdown("""
    ### 📖 MedVerify Technical Architecture
    MedVerify was engineered to resolve the two central vulnerabilities of clinical AI: **uncontrolled token expense** and **dangerous contextual hallucination**.

    #### Core Innovations:
    1. **Adaptive Query Router:** Classifies queries into `DIRECT_ANSWER` (bypasses retrieval), `CLINICAL_RETRIEVAL` (triggers hybrid search), or `MULTI_HOP` (decomposes query).
    2. **Neural Cross-Encoder Reranking:** BM25 (sparse lexical) and dense vector candidates are merged via Reciprocal Rank Fusion (RRF), then re-scored by a Cross-Encoder to prune distractors.
    3. **Proposition-Level NLI Guardrail:** The generated answer is decomposed into atomic clinical assertions and verified against cited PubMed abstracts via Natural Language Inference (`Entailment`, `Neutral`, `Contradiction`).
    4. **Telemetry Engine:** Tracks real-time token savings, latency waterfalls, and rank shifts.
    """)
