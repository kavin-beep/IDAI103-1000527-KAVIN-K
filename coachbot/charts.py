"""Neon-styled Plotly visualisations for CoachBot plans and logs."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from coachbot.schema import CoachPlan

LIME, CYAN, PINK, VIOLET, AMBER = "#C6FF3D", "#3DF5FF", "#FF3DAE", "#9D7BFF", "#FFB13D"
FONT = dict(family="Space Grotesk, Inter, sans-serif", color="#E9F0FF", size=13)


def _base(fig: go.Figure, height: int = 340, title: str = "") -> go.Figure:
    fig.update_layout(
        height=height, title=dict(text=title, font=dict(size=15, color="#E9F0FF"), x=0.02),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=FONT,
        margin=dict(l=10, r=10, t=44 if title else 10, b=10),
        hoverlabel=dict(bgcolor="#0B1020", bordercolor=LIME, font=FONT),
        legend=dict(orientation="h", y=-0.15, bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,.06)", zerolinecolor="rgba(255,255,255,.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.06)", zerolinecolor="rgba(255,255,255,.1)")
    return fig


def weekly_load(plan: CoachPlan) -> go.Figure:
    days = [d.day for d in plan.weekly_plan]
    fig = go.Figure()
    fig.add_bar(x=days, y=[d.duration_min for d in plan.weekly_plan], name="Minutes",
                marker=dict(color=[d.intensity for d in plan.weekly_plan], colorscale=[[0, "#1B2340"], [0.5, CYAN], [1, LIME]],
                            line=dict(width=0)), hovertext=[d.focus for d in plan.weekly_plan])
    fig.add_scatter(x=days, y=[d.intensity for d in plan.weekly_plan], name="Intensity (0-10)", yaxis="y2",
                    mode="lines+markers", line=dict(color=PINK, width=3, shape="spline"),
                    marker=dict(size=10, color=PINK, line=dict(color="#fff", width=1.5)))
    fig.update_layout(yaxis=dict(title="Minutes"), yaxis2=dict(title="Intensity", overlaying="y", side="right",
                                                                 range=[0, 10.5], showgrid=False), bargap=0.35)
    fig = _base(fig, title="⚡ Weekly training load")
    fig.update_layout(margin=dict(l=60, r=60, t=44, b=10))
    return fig


def load_landscape(plan: CoachPlan) -> go.Figure:
    """3D surface: how effort flows across the week and through each session's phases."""
    days = [d.day for d in plan.weekly_plan] or ["Mon"]
    phases = ["Warm-up", "Build", "Peak", "Skill", "Cool-down"]
    curve = np.array([0.35, 0.7, 1.0, 0.75, 0.25])
    intens = np.array([d.intensity for d in plan.weekly_plan] or [0], dtype=float)
    z = np.outer(curve, intens)
    fig = go.Figure(go.Surface(
        z=z, x=list(range(len(days))), y=list(range(len(phases))),
        colorscale=[[0, "#0A0F24"], [0.3, VIOLET], [0.65, CYAN], [1, LIME]], showscale=False,
        contours=dict(z=dict(show=True, usecolormap=True, project_z=True, width=2)),
        lighting=dict(ambient=0.55, diffuse=0.9, specular=0.6, roughness=0.35), opacity=0.96,
        hovertemplate="%{z:.1f} effort<extra></extra>",
    ))
    axis = dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,.08)", showbackground=True,
                zerolinecolor="rgba(255,255,255,.1)")
    fig.update_layout(scene=dict(
        xaxis=dict(axis, title="", tickvals=list(range(len(days))), ticktext=days),
        yaxis=dict(axis, title="", tickvals=list(range(len(phases))), ticktext=phases),
        zaxis=dict(axis, title="Effort"),
        camera=dict(eye=dict(x=1.6, y=-1.5, z=0.9)), aspectratio=dict(x=1.4, y=1, z=0.6),
    ))
    return _base(fig, height=420, title="🌋 3D effort landscape")


def focus_radar(plan: CoachPlan) -> go.Figure:
    names = [f.name for f in plan.focus_areas] or ["Focus"]
    scores = [f.score for f in plan.focus_areas] or [0]
    fig = go.Figure(go.Scatterpolar(
        r=scores + scores[:1], theta=names + names[:1], fill="toself",
        fillcolor="rgba(61,245,255,.18)", line=dict(color=CYAN, width=3), marker=dict(color=LIME, size=8),
    ))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, 10], gridcolor="rgba(255,255,255,.1)", showticklabels=False),
                                 angularaxis=dict(gridcolor="rgba(255,255,255,.1)")), showlegend=False)
    return _base(fig, title="🎯 What this plan develops")


def macro_donut(plan: CoachPlan) -> go.Figure:
    m = plan.macros
    fig = go.Figure(go.Pie(
        labels=["Protein", "Carbs", "Fat"], values=[m.protein_pct, m.carbs_pct, m.fat_pct], hole=0.68,
        marker=dict(colors=[PINK, LIME, AMBER], line=dict(color="#05070F", width=4)),
        textinfo="label+percent", sort=False,
    ))
    fig.add_annotation(text=f"<b>{m.calories}</b><br>kcal / day", showarrow=False, font=dict(size=18, color="#fff"))
    fig.update_layout(showlegend=False)
    return _base(fig, title="🍽️ Daily fuel split")


def compare_bars(rows: list[dict], metric: str, title: str) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=[r["label"] for r in rows], y=[r[metric] for r in rows],
        marker=dict(color=[LIME, CYAN, PINK, VIOLET, AMBER][: len(rows)]), text=[r[metric] for r in rows],
        textposition="outside", cliponaxis=False,
    ))
    fig.update_yaxes(showticklabels=False, rangemode="tozero")
    return _base(fig, height=280, title=title)


def log_timeline(df) -> go.Figure:
    fig = go.Figure()
    colors = {"ok": LIME, "demo": CYAN, "blocked": AMBER, "error": PINK}
    for status, grp in df.groupby("status"):
        fig.add_scatter(x=grp["ts"], y=grp["latency_s"], mode="markers", name=status,
                        marker=dict(size=11, color=colors.get(status, "#fff"), line=dict(color="#fff", width=1)),
                        text=grp["feature"], hovertemplate="%{text}<br>%{y:.2f}s<extra></extra>")
    fig.update_yaxes(title="Latency (s)")
    return _base(fig, title="⏱️ Latency per request")


def temperature_scatter3d(df) -> go.Figure:
    fig = go.Figure(go.Scatter3d(
        x=df["temperature"], y=df["top_p"], z=df["output_chars"], mode="markers",
        marker=dict(size=6, color=df["latency_s"], colorscale=[[0, CYAN], [1, PINK]], opacity=0.9,
                    line=dict(color="#fff", width=0.5)),
        text=df["feature"], hovertemplate="%{text}<br>T=%{x} top_p=%{y}<br>%{z} chars<extra></extra>",
    ))
    axis = dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,.08)")
    fig.update_layout(scene=dict(xaxis=dict(axis, title="temperature"), yaxis=dict(axis, title="top_p"),
                                 zaxis=dict(axis, title="output chars")))
    return _base(fig, height=420, title="🧪 Sampling space explored")
