"""
MedVerify: Clinical Evidence & Drug Research Copilot
Obsidian Dark & Indigo Glassmorphism UI (Matched with ShortLink-Service).
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
    page_title="MedVerify | Clinical RAG & Guardrails",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- OBSIDIAN GLASS THEME (Matched directly with ShortLink-Service index.css) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Obsidian Palette */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
    }

    .stApp {
        background-color: #0b0d13 !important;
        color: #f1f5f9 !important;
    }

    /* Ambient Glow Background Orbs (ShortLink-Service .bg-glow & .bg-glow-alt) */
    .stApp::before {
        content: "";
        position: fixed;
        width: 60vw;
        height: 60vw;
        top: -15%;
        left: -10%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.14) 0%, rgba(11, 13, 19, 0) 70%);
        pointer-events: none;
        z-index: 0;
    }

    .stApp::after {
        content: "";
        position: fixed;
        width: 50vw;
        height: 50vw;
        bottom: -15%;
        right: -10%;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, rgba(11, 13, 19, 0) 70%);
        pointer-events: none;
        z-index: 0;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0b0d13;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.12);
        border-radius: 9999px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.22);
    }

    /* Glass Panels & Cards */
    .glass-panel {
        background: rgba(18, 22, 34, 0.75) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6) !important;
        border-radius: 16px !important;
        padding: 20px 24px;
        margin-bottom: 20px;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-radius: 14px !important;
        padding: 16px 18px;
        transition: all 0.2s ease-in-out;
        margin-bottom: 16px;
    }

    .glass-card:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(99, 102, 241, 0.35) !important;
    }

    /* Text Gradients (ShortLink .text-gradient) */
    .text-gradient {
        background: linear-gradient(135deg, #a5b4fc 0%, #d8b4fe 50%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.02em;
    }

    .text-gradient-emerald {
        background: linear-gradient(135deg, #6ee7b7 0%, #2dd4bf 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }

    /* Hero Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.3);
        color: #a5b4fc;
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .pulsing-dot {
        width: 8px;
        height: 8px;
        background: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10B981;
    }

    /* KPI Stat Grid */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 20px;
    }

    .kpi-tile {
        background: rgba(18, 22, 34, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 18px;
        backdrop-filter: blur(12px);
    }

    .kpi-label {
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }

    .kpi-value {
        font-size: 1.5rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Inputs & Selectboxes */
    .stSelectbox div[data-baseweb="select"] {
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }

    .stTextArea textarea {
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
    }

    /* Primary Action Button (ShortLink-Service .btn-primary) */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 12px 28px -5px rgba(99, 102, 241, 0.5) !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 18px;
        font-weight: 600;
        color: #94a3b8;
        background: transparent;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.18) !important;
        color: #a5b4fc !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def load_medverify_pipeline():
    """Initializes the pipeline once and caches it in memory."""
    return MedVerifyPipeline()


# --- SIDEBAR (ShortLink Obsidian Panel) ---
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
        <span style="font-size: 2.2rem;">🩺</span>
        <div>
            <div style="font-weight: 800; font-size: 1.25rem; color: #FFFFFF; letter-spacing: -0.01em;">MedVerify</div>
            <div style="font-size: 0.72rem; color: #818cf8; font-weight: 600; letter-spacing: 0.05em;">CLINICAL RAG WORKBENCH</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("##### ⚙️ LLM Runtime Engine")
    provider = st.selectbox(
        "Execution Mode",
        ["mock", "gemini", "openai"],
        format_func=lambda x: {
            "mock": "⚡ Zero-Setup Demo (Local Neural)",
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
    st.markdown("##### 🧪 Select Clinical Benchmark")

    sample_queries = [
        "Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?",
        "What is the recommended dose adjustment for Apixaban in patients with severe renal impairment?",
        "Do preoperative statins reduce the incidence of postoperative atrial fibrillation after coronary artery bypass grafting?",
        "Does routine hydroxychloroquine administration improve clinical recovery in hospitalized COVID-19 patients?",
        "What is essential hypertension?",
        "In a diabetic patient with eGFR of 35 mL/min and a history of atrial fibrillation, can Metformin and Apixaban be co-administered safely?"
    ]

    selected_sample = st.selectbox("Clinical Scenario:", sample_queries)
    custom_query = st.text_area("Question to Analyze:", value=selected_sample, height=85)

    execute_btn = st.button("🚀 Run Cognitive Pipeline", use_container_width=True)

    st.markdown("""
    <div style="font-size: 0.76rem; color: #64748B; margin-top: 24px; line-height: 1.5;">
        <div style="font-weight: 600; color: #94A3B8; margin-bottom: 4px;">ACTIVE GUARDRAILS:</div>
        • <strong>Routing:</strong> Dynamic Complexity Gate<br>
        • <strong>Reranker:</strong> Neural Cross-Encoder<br>
        • <strong>Auditor:</strong> Claim-Level NLI Verifier<br>
        • <strong>Corpus:</strong> PubMedQA Clinical Trials
    </div>
    """, unsafe_allow_html=True)


# --- HERO SECTION ---
st.markdown("""
<div class="status-badge">
    <div class="pulsing-dot"></div>
    Adaptive Guardrail System Active • Latency Optimized
</div>
<div style="font-size: 2.4rem;" class="text-gradient">MedVerify Clinical Copilot</div>
<div style="font-size: 0.98rem; color: #94a3b8; margin-bottom: 24px; line-height: 1.5;">
    Evidence-grounded medical decision support with adaptive retrieval gating, neural cross-encoder reranking, and proposition-level hallucination verification.
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "📊 Live Copilot & Observability",
    "🔬 3-Way Baseline Benchmark (No-RAG vs Fixed vs MedVerify)",
    "📖 Architecture & Verification Spec"
])

# Initialize Pipeline
pipeline = load_medverify_pipeline()
if provider != pipeline.generator.provider or (api_key and api_key != pipeline.generator.api_key):
    pipeline.generator.provider = provider
    pipeline.generator.api_key = api_key

# Run or Load Results
if "analysis_result" not in st.session_state or execute_btn:
    query_to_run = custom_query if custom_query.strip() else selected_sample
    with st.spinner("Executing MedVerify cognitive pipeline..."):
        st.session_state.analysis_result = pipeline.run_adaptive_pipeline(query_to_run)
        st.session_state.benchmark_result = pipeline.run_baseline_comparison(query_to_run)

res = st.session_state.analysis_result
bench = st.session_state.benchmark_result


# --- TAB 1: COPILOT & OBSERVABILITY ---
with tab1:
    # 4 Top KPI Metric Cards (Obsidian Glass)
    route_name = res["routing"]["route"].replace("_", " ")
    faith_pct = int(res["audit_result"]["faithfulness_score"] * 100)
    saved_pct = res["cost_savings"]["percentage_tokens_saved"]
    latency_sec = res["total_execution_time_s"]

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-tile">
            <div class="kpi-label">1. Adaptive Decision</div>
            <div class="kpi-value" style="color: #818cf8;">{route_name}</div>
        </div>
        <div class="kpi-tile">
            <div class="kpi-label">2. Faithfulness Score</div>
            <div class="kpi-value" style="color: {'#34D399' if faith_pct >= 70 else '#FBBF24'};">{faith_pct}%</div>
        </div>
        <div class="kpi-tile">
            <div class="kpi-label">3. Tokens Saved vs Fixed</div>
            <div class="kpi-value" style="color: #c084fc;">{saved_pct}%</div>
        </div>
        <div class="kpi-tile">
            <div class="kpi-label">4. End-to-End Latency</div>
            <div class="kpi-value" style="color: #f1f5f9;">{latency_sec}s</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1.15, 0.85], gap="large")

    # LEFT COLUMN: Doctor's View
    with col_left:
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 1.15rem; color: #FFFFFF;">📋 Verified Clinical Synthesis</span>
            <span style="font-size: 0.76rem; color: #818cf8; background: rgba(99,102,241,0.12); padding: 3px 10px; border-radius: 9999px; border: 1px solid rgba(99,102,241,0.3);">
                Claim-Level NLI Verified
            </span>
        </div>
        """, unsafe_allow_html=True)

        highlighted_html = render_claim_highlighted_html(res["audit_result"]["claim_audits"])
        st.markdown(f"""
        <div class="glass-panel" style="border-left: 4px solid #6366f1 !important;">
            <div style="font-size: 0.82rem; color: #94A3B8; margin-bottom: 14px; font-weight: 600;">
                QUERY: <span style="color: #F8FAFC;">{res['query']}</span>
            </div>
            {highlighted_html}
        </div>
        """, unsafe_allow_html=True)

        if res["audit_result"]["has_hallucination"]:
            st.error("🛡️ **Guardrail Intervention:** MedVerify identified ungrounded or contradicted claims in the preliminary synthesis and applied self-correction.")

        # Evidence Drawer
        with st.expander(f"📚 Cited PubMed Evidence Dossier ({len(res['reranked_docs'])} studies retained)", expanded=True):
            if res["reranked_docs"]:
                for i, doc in enumerate(res["reranked_docs"], start=1):
                    delta = doc.get("rank_delta", 0)
                    delta_color = "#34D399" if delta > 0 else ("#FB7185" if delta < 0 else "#94A3B8")
                    delta_str = f"+{delta}" if delta > 0 else f"{delta}"

                    st.markdown(f"""
                    <div class="glass-card" style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 700; color: #818cf8; font-size: 0.92rem;">
                                Reference [{i}] • PMID: {doc['pmid']}
                            </span>
                            <span style="font-size: 0.75rem; background: rgba(255,255,255,0.06); padding: 3px 8px; border-radius: 6px; font-family: monospace;">
                                Cross-Encoder Score: <strong>{doc.get('raw_rerank_score', 0):.3f}</strong> 
                                (<span style="color: {delta_color}; font-weight: 700;">Rank {delta_str}</span>)
                            </span>
                        </div>
                        <div style="font-size: 0.88rem; font-weight: 600; color: #E2E8F0; margin-bottom: 6px;">
                            {doc['question']}
                        </div>
                        <div style="font-size: 0.82rem; color: #94A3B8; line-height: 1.6; white-space: pre-line;">
                            {doc['content'][:360]}...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ No external literature retrieved: Query was answered directly through parametric memory (Definitional Route).")

    # RIGHT COLUMN: Observability Telemetry
    with col_right:
        st.markdown('<div style="font-weight: 700; font-size: 1.15rem; color: #FFFFFF; margin-bottom: 8px;">🛡️ Real-Time Telemetry Inspector</div>', unsafe_allow_html=True)

        # 1. Routing Gate
        r_info = res["routing"]
        st.markdown(f"""
        <div class="glass-panel" style="padding: 16px 18px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.8rem; font-weight: 700; color: #818cf8; text-transform: uppercase;">1. Adaptive Routing Gate</span>
                <span style="font-size: 0.75rem; color: #94A3B8; font-family: monospace;">{r_info['decision_latency_ms']} ms</span>
            </div>
            <div style="font-size: 0.85rem; color: #CBD5E1; margin-bottom: 8px; line-height: 1.5;">
                {r_info['reasoning']}
            </div>
            <div style="font-size: 0.78rem; color: #94A3B8;">Confidence: <strong style="color: #6ee7b7;">{int(r_info['confidence']*100)}%</strong></div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Neural Reranker Shift Chart
        st.markdown("""
        <div class="glass-panel" style="padding: 16px 18px; margin-bottom: 16px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #c084fc; text-transform: uppercase; margin-bottom: 8px;">
                2. Cross-Encoder Rank-Shift Delta
            </div>
        """, unsafe_allow_html=True)
        if res["rerank_telemetry"].get("rank_shifts"):
            fig_rerank = create_rank_shift_chart(res["rerank_telemetry"]["rank_shifts"])
            st.plotly_chart(fig_rerank, use_container_width=True)
            st.caption(f"Retained top {res['rerank_telemetry']['candidates_retained']} chunks; dropped {res['rerank_telemetry']['candidates_pruned']} distractor chunks.")
        else:
            st.caption("Direct Answer route active. Cross-Encoder bypassed to save compute.")
        st.markdown("</div>", unsafe_allow_html=True)

        # 3. Latency Waterfall Chart
        st.markdown("""
        <div class="glass-panel" style="padding: 16px 18px; margin-bottom: 16px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #34d399; text-transform: uppercase; margin-bottom: 8px;">
                3. End-to-End Latency Waterfall
            </div>
        """, unsafe_allow_html=True)
        fig_waterfall = create_latency_waterfall_chart(res["latency_waterfall"])
        st.plotly_chart(fig_waterfall, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 4. Detailed Claim Audit Table
        with st.expander("📋 Proposition Audit Breakdown (NLI)"):
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
        <div class="glass-panel" style="border-top: 3px solid #64748B !important;">
            <div style="font-weight: 700; font-size: 1.05rem; color: #94A3B8; margin-bottom: 12px;">1️⃣ No-RAG (Parametric)</div>
            <div style="font-size: 0.86rem; line-height: 2.1;">
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
        <div class="glass-panel" style="border-top: 3px solid #F59E0B !important;">
            <div style="font-weight: 700; font-size: 1.05rem; color: #FBBF24; margin-bottom: 12px;">2️⃣ Fixed-RAG (Naive Top-5)</div>
            <div style="font-size: 0.86rem; line-height: 2.1;">
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
        <div class="glass-panel" style="border-top: 3px solid #6366f1 !important;">
            <div style="font-weight: 700; font-size: 1.05rem; color: #818cf8; margin-bottom: 12px;">3️⃣ MedVerify (Adaptive) 🏆</div>
            <div style="font-size: 0.86rem; line-height: 2.1;">
                <div>Faithfulness: <strong style="color: #34D399;">{int(b_med['faithfulness']*100)}% (Highest)</strong></div>
                <div>Hallucinated Claims: <strong style="color: #34D399;">{b_med['hallucinations_detected']} (Protected)</strong></div>
                <div>Tokens Consumed: <strong style="color: #818cf8;">{b_med['total_tokens']} (Saved {b_med['tokens_saved_pct']}%)</strong></div>
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


# --- TAB 3: SPEC & AUDIT ---
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
