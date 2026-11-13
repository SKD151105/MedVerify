"""
Visualizer and HTML rendering components for MedVerify UI.
High-end Glassmorphic / Modern Clinical Telemetry Design.
"""

from typing import List, Dict, Any
import plotly.graph_objects as go


def render_claim_highlighted_html(claim_audits: List[Dict[str, Any]]) -> str:
    """Renders clinical answer with sleek modern sentence-level audit highlights and badge pills."""
    html_spans = []
    for item in claim_audits:
        claim_text = item["claim"]
        label = item["label"]
        pmid = item["cited_pmid"]
        conf = item["confidence"]

        if label == "ENTAILMENT":
            bg_color = "rgba(16, 185, 129, 0.08)"
            border_color = "#10B981"
            text_color = "#E2E8F0"
            badge_html = (
                f'<span style="background: rgba(16, 185, 129, 0.18); border: 1px solid rgba(16, 185, 129, 0.45); '
                f'color: #34D399; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 600; '
                f'margin-left: 8px; display: inline-flex; align-items: center; gap: 4px; vertical-align: middle;">'
                f'<span style="width: 6px; height: 6px; border-radius: 50%; background-color: #34D399;"></span>'
                f'Entailed ({int(conf*100)}%)</span>'
            )
        elif label == "NEUTRAL":
            bg_color = "rgba(245, 158, 11, 0.08)"
            border_color = "#F59E0B"
            text_color = "#E2E8F0"
            badge_html = (
                f'<span style="background: rgba(245, 158, 11, 0.18); border: 1px solid rgba(245, 158, 11, 0.45); '
                f'color: #FBBF24; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 600; '
                f'margin-left: 8px; display: inline-flex; align-items: center; gap: 4px; vertical-align: middle;">'
                f'<span style="width: 6px; height: 6px; border-radius: 50%; background-color: #FBBF24;"></span>'
                f'Extrapolated ({int(conf*100)}%)</span>'
            )
        else:
            bg_color = "rgba(244, 63, 94, 0.08)"
            border_color = "#F43F5E"
            text_color = "#FECDD3"
            badge_html = (
                f'<span style="background: rgba(244, 63, 94, 0.18); border: 1px solid rgba(244, 63, 94, 0.45); '
                f'color: #FB7185; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 600; '
                f'margin-left: 8px; display: inline-flex; align-items: center; gap: 4px; vertical-align: middle;">'
                f'<span style="width: 6px; height: 6px; border-radius: 50%; background-color: #FB7185;"></span>'
                f'Hallucination Blocked</span>'
            )

        citation_pill = ""
        if pmid != "None" and pmid != "UNKNOWN":
            citation_pill = (
                f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank" style="text-decoration: none;">'
                f'<span style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); '
                f'color: #38BDF8; padding: 2px 7px; border-radius: 4px; font-size: 0.72rem; font-family: monospace; '
                f'margin-left: 6px; vertical-align: middle;">PMID:{pmid} ↗</span></a>'
            )

        span = f"""
        <div style="background: {bg_color}; border-left: 3px solid {border_color}; padding: 10px 14px; margin-bottom: 10px; border-radius: 6px; line-height: 1.65; color: {text_color}; font-size: 0.95rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <span>{claim_text}</span> {badge_html} {citation_pill}
        </div>
        """
        html_spans.append(span)

    return "".join(html_spans)


def create_latency_waterfall_chart(latency_waterfall: Dict[str, float]) -> go.Figure:
    """Creates a horizontal bar chart of the pipeline latency breakdown."""
    stages = [k for k in latency_waterfall.keys() if k != "Total Pipeline Latency"]
    values = [latency_waterfall[k] for k in stages]

    colors = [
        '#38BDF8',  # Sky Blue (Routing)
        '#818CF8',  # Indigo (Retrieval)
        '#C084FC',  # Purple (Reranking)
        '#34D399',  # Emerald (Synthesis)
        '#F43F5E'   # Rose (Verification)
    ]

    fig = go.Figure(go.Bar(
        x=values,
        y=stages,
        orientation='h',
        marker=dict(
            color=colors[:len(stages)],
            line=dict(color='rgba(255,255,255,0.15)', width=1)
        ),
        text=[f"{v} ms" for v in values],
        textposition='outside',
        textfont=dict(color='#E2E8F0', size=11, family='JetBrains Mono, monospace')
    ))

    fig.update_layout(
        margin=dict(l=10, r=40, t=10, b=10),
        height=240,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.06)',
            tickfont=dict(color='#94A3B8', size=10),
            title=dict(text="Execution Latency (ms)", font=dict(color='#94A3B8', size=11))
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(color='#CBD5E1', size=11)
        )
    )
    return fig


def create_rank_shift_chart(rank_shifts: List[Dict[str, Any]]) -> go.Figure:
    """Creates a slope/scatter chart visualizing rank shifts between Hybrid and Cross-Encoder."""
    if not rank_shifts:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text="Direct Answer Route: Retrieval Bypassed", showarrow=False, font=dict(color="#94A3B8", size=13))],
            height=220
        )
        return fig

    fig = go.Figure()

    for d in rank_shifts:
        pmid = f"PMID {d['pmid']}"
        init_r = d["initial_rank"]
        rerank_r = d["reranked_rank"]
        delta = init_r - rerank_r
        color = "#10B981" if delta > 0 else ("#F43F5E" if delta < 0 else "#64748B")

        fig.add_trace(go.Scatter(
            x=["Initial Hybrid Rank", "Cross-Encoder Rank"],
            y=[init_r, rerank_r],
            mode="lines+markers+text",
            name=pmid,
            text=[f"#{init_r}", f"#{rerank_r} ({'+' if delta > 0 else ''}{delta})"],
            textposition=["middle left", "middle right"],
            textfont=dict(color='#E2E8F0', size=11, family='JetBrains Mono, monospace'),
            line=dict(color=color, width=3),
            marker=dict(size=9, color=color, line=dict(color='#FFFFFF', width=1.5))
        ))

    fig.update_layout(
        margin=dict(l=20, r=40, t=20, b=20),
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            autorange="reversed",
            dtick=1,
            showgrid=True,
            gridcolor='rgba(255,255,255,0.06)',
            tickfont=dict(color='#94A3B8', size=10),
            title=dict(text="Rank Position (1 is Highest)", font=dict(color='#94A3B8', size=11))
        ),
        xaxis=dict(
            tickfont=dict(color='#E2E8F0', size=11, weight='bold')
        ),
        showlegend=False
    )
    return fig
