"""
MedVerify: Clinical Evidence & Drug Research Copilot
Streamlit Interactive Application with Real-Time Observability and Guardrails.
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
    page_title="MedVerify | Clinical Evidence Copilot",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #78909C;
        margin-bottom: 18px;
    }
    .metric-card {
        background-color: #1E293B;
        border-radius: 8px;
        padding: 14px;
        border-left: 4px solid #1E88E5;
        margin-bottom: 12px;
    }
    .evidence-box {
        background-color: #0F172A;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_pipeline(provider: str, api_key: str):
    return MedVerifyPipeline(llm_provider=provider, api_key=api_key)


# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/medical-heart.png", width=64)
    st.markdown("### **MedVerify Control Center**")
    st.caption("Adaptive RAG • Cross-Encoder • NLI Guardrail")
    st.divider()

    provider = st.selectbox(
        "LLM Provider",
        ["mock", "gemini", "openai"],
        format_func=lambda x: {
            "mock": "⚡ Demo Mode (Offline / Fast)",
            "gemini": "✨ Google Gemini API",
            "openai": "🤖 OpenAI API"
        }[x]
    )

    api_key = ""
    if provider in ["gemini", "openai"]:
        api_key = st.text_input(
            f"{provider.upper()} API Key",
            type="password",
            help=f"Enter your {provider} API key. In demo mode, no key is required."
        )

    st.divider()
    st.markdown("#### 🧪 Select Clinical Benchmark Query")

    sample_queries = [
        "Does Metformin reduce cardiovascular mortality in patients with chronic kidney disease?",
        "What is the recommended dose adjustment for Apixaban in patients with severe renal impairment?",
        "Do preoperative statins reduce the incidence of postoperative atrial fibrillation after coronary artery bypass grafting?",
        "Does routine hydroxychloroquine administration improve clinical recovery in hospitalized COVID-19 patients?",
        "What is essential hypertension?",
        "In a diabetic patient with eGFR of 35 mL/min and a history of atrial fibrillation, can Metformin and Apixaban be co-administered safely?"
    ]

    selected_sample = st.selectbox("Choose a test case:", sample_queries)
    custom_query = st.text_area("Or enter a custom clinical query:", value=selected_sample, height=90)

    execute_btn = st.button("🚀 Analyze Query", type="primary", use_container_width=True)
    st.caption("Benchmark tested against PubMedQA dataset.")


# --- MAIN VIEW ---
st.markdown('<div class="main-header">🩺 MedVerify Copilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Clinical Evidence Synthesis with Adaptive Retrieval, Neural Reranking, and Claim-Level Hallucination Guardrails</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs([
    "📊 Live Clinical Copilot & Guardrails",
    "🔬 3-Way Baseline Benchmark (No-RAG vs Fixed vs MedVerify)",
    "📖 Architecture & Technical Specs"
])

# Initialize Pipeline
pipeline = get_pipeline(provider=provider, api_key=api_key)

if "last_query" not in st.session_state:
    st.session_state.last_query = selected_sample

if execute_btn or "analysis_result" not in st.session_state:
    query_to_run = custom_query if custom_query.strip() else selected_sample
    st.session_state.last_query = query_to_run
    with st.spinner("Executing MedVerify cognitive pipeline (Routing -> Retrieval -> Reranking -> Synthesis -> NLI Audit)..."):
        st.session_state.analysis_result = pipeline.run_adaptive_pipeline(query_to_run)
        st.session_state.benchmark_result = pipeline.run_baseline_comparison(query_to_run)

res = st.session_state.analysis_result
bench = st.session_state.benchmark_result

# --- TAB 1: COPILOT VIEW ---
with tab1:
    col_left, col_right = st.columns([1.1, 0.9], gap="large")

    # LEFT COLUMN: Doctor's View
    with col_left:
        st.markdown(f"#### ❓ Clinical Question")
        st.info(f"**{res['query']}**")

        st.markdown("#### 📝 Evidence-Grounded Synthesis")
        st.caption("Each proposition is audited against PubMed abstracts: 🟢 Entailed | 🟡 Extrapolated | 🔴 Contradicted / Flagged")

        highlighted_html = render_claim_highlighted_html(res["audit_result"]["claim_audits"])
        st.markdown(f"""
        <div style="background-color: #1E293B; border-radius: 8px; padding: 18px; border: 1px solid #334155; margin-bottom: 18px;">
            {highlighted_html}
        </div>
        """, unsafe_allow_html=True)

        if res["audit_result"]["has_hallucination"]:
            st.warning("⚠️ **Guardrail Notice:** MedVerify detected ungrounded or contradicted claims and automatically activated the self-correction protocol.")

        # Evidence Drawer
        with st.expander(f"📚 Retrieved Evidence Dossier ({len(res['reranked_docs'])} studies retained)", expanded=True):
            if res["reranked_docs"]:
                for i, doc in enumerate(res["reranked_docs"], start=1):
                    delta = doc.get("rank_delta", 0)
                    delta_str = f"+{delta}" if delta > 0 else f"{delta}"
                    st.markdown(f"""
                    <div class="evidence-box">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 600; color: #60A5FA;">[Study #{i}] PMID: {doc['pmid']}</span>
                            <span style="font-size: 0.8rem; background-color: #334155; padding: 2px 8px; border-radius: 4px;">
                                Rerank Score: {doc.get('raw_rerank_score', 0):.3f} (Rank Shift: {delta_str})
                            </span>
                        </div>
                        <div style="font-size: 0.9rem; color: #CBD5E1; margin-top: 6px;">
                            <strong>Research Question:</strong> {doc['question']}
                        </div>
                        <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 6px; white-space: pre-line;">
                            {doc['content'][:400]}...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No external literature retrieved (Query answered directly via parametric memory).")

    # RIGHT COLUMN: Observability Telemetry
    with col_right:
        st.markdown("#### 🛡️ Guardrails & Observability Telemetry")

        # Metric Tiles
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Route Taken", res["routing"]["route"].replace("_", " "))
        m2.metric("Faithfulness", f"{int(res['audit_result']['faithfulness_score'] * 100)}%")
        m3.metric("Tokens Saved", f"{res['cost_savings']['percentage_tokens_saved']}%")
        m4.metric("Latency", f"{res['total_execution_time_s']}s")

        st.divider()

        # 1. Routing Telemetry
        st.markdown("##### ⚡ Adaptive Routing Gate")
        r_info = res["routing"]
        st.caption(f"Reasoning: {r_info['reasoning']}")
        st.progress(r_info["confidence"], text=f"Routing Confidence: {int(r_info['confidence']*100)}%")

        # 2. Neural Reranker Shift Chart
        st.markdown("##### 🔍 Cross-Encoder Reranking Telemetry")
        if res["rerank_telemetry"].get("rank_shifts"):
            fig_rerank = create_rank_shift_chart(res["rerank_telemetry"]["rank_shifts"])
            st.plotly_chart(fig_rerank, use_container_width=True)
            st.caption(f"Retained {res['rerank_telemetry']['candidates_retained']} high-relevance studies; pruned {res['rerank_telemetry']['candidates_pruned']} low-scoring distractor chunks.")
        else:
            st.info("Direct answer mode active. Neural reranker bypassed to conserve compute.")

        # 3. Latency Waterfall Chart
        st.markdown("##### ⏱️ Pipeline Latency Waterfall")
        fig_waterfall = create_latency_waterfall_chart(res["latency_waterfall"])
        st.plotly_chart(fig_waterfall, use_container_width=True)

        # 4. Detailed Claim Audit Table
        with st.expander("📋 Detailed Claim-by-Claim NLI Table"):
            audit_df = pd.DataFrame(res["audit_result"]["claim_audits"])[["claim", "label", "confidence", "cited_pmid"]]
            st.dataframe(audit_df, use_container_width=True)


# --- TAB 2: BASELINE BENCHMARK ---
with tab2:
    st.markdown("### 🔬 3-Way Comparative Benchmark on Current Query")
    st.write("Comparing **No-RAG** (Parametric), **Naive Fixed-RAG** (Blind Top-5), and **MedVerify** (Adaptive + Reranker + Guardrail).")

    b_no = bench["no_rag"]
    b_fix = bench["fixed_rag"]
    b_med = bench["medverify"]

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("#### 1️⃣ No-RAG (Parametric LLM)")
        st.markdown(f"**Faithfulness:** `{int(b_no['faithfulness']*100)}%`")
        st.markdown(f"**Hallucinated Claims:** `{b_no['hallucinations_detected']}`")
        st.markdown(f"**Tokens Consumed:** `{b_no['total_tokens']}`")
        st.markdown(f"**Latency:** `{b_no['latency_s']}s`")
        st.markdown(f"**Retrieved Chunks:** `{b_no['retrieved_docs_count']}`")
        with st.expander("Generated Output"):
            st.caption(b_no["answer"])

    with c2:
        st.markdown("#### 2️⃣ Fixed-RAG (Naive Top-5)")
        st.markdown(f"**Faithfulness:** `{int(b_fix['faithfulness']*100)}%`")
        st.markdown(f"**Hallucinated Claims:** `{b_fix['hallucinations_detected']}`")
        st.markdown(f"**Tokens Consumed:** `{b_fix['total_tokens']}` (Highest)")
        st.markdown(f"**Latency:** `{b_fix['latency_s']}s`")
        st.markdown(f"**Retrieved Chunks:** `{b_fix['retrieved_docs_count']}` (Fixed)")
        with st.expander("Generated Output"):
            st.caption(b_fix["answer"])

    with c3:
        st.markdown("#### 3️⃣ MedVerify (Adaptive + Guardrail)")
        st.markdown(f"**Faithfulness:** `{int(b_med['faithfulness']*100)}%` 🏆")
        st.markdown(f"**Hallucinated Claims:** `{b_med['hallucinations_detected']}` (Shielded)")
        st.markdown(f"**Tokens Consumed:** `{b_med['total_tokens']}` (**Saved {b_med['tokens_saved_pct']}%**)")
        st.markdown(f"**Latency:** `{b_med['latency_s']}s`")
        st.markdown(f"**Retrieved Chunks:** `{b_med['retrieved_docs_count']}` (Pruned)")
        with st.expander("Generated Output"):
            st.caption(b_med["answer"])

    st.divider()

    # Benchmark Summary Table
    comparison_data = {
        "Metric": ["Faithfulness Score", "Hallucinated Claims", "Tokens Consumed", "Latency (s)", "Retrieved Passages"],
        "No-RAG": [f"{int(b_no['faithfulness']*100)}%", b_no["hallucinations_detected"], b_no["total_tokens"], b_no["latency_s"], b_no["retrieved_docs_count"]],
        "Fixed-RAG (Naive)": [f"{int(b_fix['faithfulness']*100)}%", b_fix["hallucinations_detected"], b_fix["total_tokens"], b_fix["latency_s"], b_fix["retrieved_docs_count"]],
        "MedVerify (Adaptive)": [f"{int(b_med['faithfulness']*100)}%", b_med["hallucinations_detected"], b_med["total_tokens"], b_med["latency_s"], b_med["retrieved_docs_count"]]
    }
    st.table(pd.DataFrame(comparison_data))


# --- TAB 3: SPECS & ABOUT ---
with tab3:
    st.markdown("### 📖 MedVerify Technical Specification")
    st.markdown("""
    MedVerify was designed to eliminate the two greatest vulnerabilities of Generative AI in healthcare:
    1. **Blind Token Expenditure:** Fixed-RAG pipelines retrieve documents regardless of query necessity.
    2. **Unverified Clinical Hallucinations:** Generative models often assert unsupported clinical statements.

    #### Pipeline Components:
    * **Dataset:** Evaluated against **PubMedQA** (expert-annotated biomedical literature).
    * **Hybrid Retrieval:** Sparse lexical matching (**BM25Okapi**) combined with dense vector representations (**Sentence Transformers**).
    * **Neural Reranking:** Joint cross-attention reranker (**Cross-Encoder / ms-marco-MiniLM**) filters distractor passages.
    * **Claim-Level Guardrail:** Proposition decomposition evaluated by **Natural Language Inference (NLI)** into *Entailment*, *Neutral*, and *Contradiction*.
    """)
