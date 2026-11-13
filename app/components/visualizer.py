"""
Visualizer and HTML rendering components for MedVerify UI.
"""

from typing import List, Dict, Any
import plotly.graph_objects as go


def render_claim_highlighted_html(claim_audits: List[Dict[str, Any]]) -> str:
    """Renders clinical answer with green/yellow/red sentence-level audit highlights."""
    html_spans = []
    for item in claim_audits:
        claim_text = item["claim"]
        label = item["label"]
        pmid = item["cited_pmid"]
        conf = item["confidence"]

        if label == "ENTAILMENT":
            bg_color = "rgba(40, 167, 69, 0.15)"
            border_color = "#28a745"
            badge = f'<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-left: 6px;">🟢 Entailed ({int(conf*100)}%)</span>'
        elif label == "NEUTRAL":
            bg_color = "rgba(255, 193, 7, 0.15)"
            border_color = "#ffc107"
            badge = f'<span style="background-color: #d39e00; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-left: 6px;">🟡 Extrapolated ({int(conf*100)}%)</span>'
        else:
            bg_color = "rgba(220, 53, 69, 0.15)"
            border_color = "#dc3545"
            badge = f'<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-left: 6px;">🔴 Hallucination Blocked</span>'

        span = f"""
        <span style="background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 6px 10px; margin-bottom: 8px; display: inline-block; border-radius: 4px; line-height: 1.6;">
            {claim_text} {badge}
        </span>
        """
        html_spans.append(span)

    return "".join(html_spans)


def create_latency_waterfall_chart(latency_waterfall: Dict[str, float]) -> go.Figure:
    """Creates a horizontal bar chart of the pipeline latency breakdown."""
    stages = [k for k in latency_waterfall.keys() if k != "Total Pipeline Latency"]
    values = [latency_waterfall[k] for k in stages]

    fig = go.Figure(go.Bar(
        x=values,
        y=stages,
        orientation='h',
        marker=dict(
            color=['#4C78A8', '#72B7B2', '#F58518', '#E45756', '#54A24B'],
            line=dict(color='rgba(255,255,255,0.2)', width=1)
        ),
        text=[f"{v} ms" for v in values],
        textposition='auto',
    ))

    fig.update_layout(
        title="Execution Latency Waterfall (ms)",
        margin=dict(l=10, r=10, t=35, b=10),
        height=260,
        xaxis_title="Time (milliseconds)",
        yaxis=dict(autorange="reversed"),
        template="plotly_dark"
    )
    return fig


def create_rank_shift_chart(rank_shifts: List[Dict[str, Any]]) -> go.Figure:
    """Creates a slope/scatter chart visualizing rank shifts between Hybrid and Cross-Encoder."""
    if not rank_shifts:
        fig = go.Figure()
        fig.update_layout(title="No documents retrieved (Direct Answer Route)", height=220)
        return fig

    pmids = [f"PMID {d['pmid']}" for d in rank_shifts]
    initial_ranks = [d["initial_rank"] for d in rank_shifts]
    reranked_ranks = [d["reranked_rank"] for d in rank_shifts]

    fig = go.Figure()

    for pmid, init_r, rerank_r in zip(pmids, initial_ranks, reranked_ranks):
        delta = init_r - rerank_r
        color = "#28a745" if delta > 0 else ("#dc3545" if delta < 0 else "#6c757d")
        fig.add_trace(go.Scatter(
            x=["Hybrid Search", "Cross-Encoder"],
            y=[init_r, rerank_r],
            mode="lines+markers+text",
            name=pmid,
            text=[f"#{init_r}", f"#{rerank_r} ({'+' if delta > 0 else ''}{delta})"],
            textposition=["middle left", "middle right"],
            line=dict(color=color, width=3),
            marker=dict(size=10)
        ))

    fig.update_layout(
        title="Neural Reranker Rank-Shift Delta",
        yaxis=dict(title="Rank (1 is best)", autorange="reversed", dtick=1),
        margin=dict(l=20, r=20, t=35, b=20),
        height=260,
        showlegend=True,
        template="plotly_dark"
    )
    return fig
