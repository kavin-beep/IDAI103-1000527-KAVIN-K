"""HTML building blocks. All model text is escaped before it reaches the page."""

from __future__ import annotations

from html import escape

import streamlit as st

from coachbot.features import CATEGORY_COLORS, FEATURES, Feature
from coachbot.schema import CoachPlan


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def heading(kicker: str, title: str, sub: str = "") -> None:
    html(f'<div class="cb-kicker">{kicker}</div><div class="cb-h">{title}</div>'
         + (f'<p class="cb-sub">{sub}</p>' if sub else ""))


def logo() -> None:
    html('<div class="cb-logo"><div class="cb-logo-orb"></div><div><b>CoachBot AI</b>'
         '<small>NEXTGEN SPORTS LAB</small></div></div>')


BADGES = (("Train", "🏋️"), ("Recover", "🩹"), ("Fuel", "🥗"), ("Mind", "🧘"), ("Tactics", "🧠"), ("Ask", "💬"))


def xp_card(xp: int, unlocked: set[str]) -> None:
    level, pct = xp // 100 + 1, xp % 100
    badges = "".join(f'<span class="cb-badge {"on" if c in unlocked else ""}" title="{c}">{e}</span>' for c, e in BADGES)
    html(f'<div class="cb-xp"><div class="cb-xp-top"><span>ATHLETE LEVEL</span><b>LV {level}</b></div>'
         f'<div class="cb-xp-bar"><i style="width:{max(pct, 4)}%"></i></div>'
         f'<div class="cb-xp-top" style="margin-top:6px"><span>{xp} XP</span><span>{100 - pct} XP to next</span></div>'
         f'<div class="cb-badges">{badges}</div></div>')


def stats(items: list[tuple[int, str, str]]) -> None:
    cards = "".join(
        f'<div class="cb-card cb-stat cb-tilt" style="--c:{c}"><div class="v" style="--to:{v}"></div><div class="l">{label}</div></div>'
        for v, label, c in items)
    html(f'<div class="cb-stats">{cards}</div>')


def marquee(words: list[str]) -> None:
    spans = "".join(f"<span>{escape(w)}</span>" for w in words * 2)
    html(f'<div class="cb-marquee"><div class="t">{spans}</div></div>')


def feature_grid(features: tuple[Feature, ...] = FEATURES) -> None:
    cards = "".join(
        f'<div class="cb-card cb-beam cb-tilt cb-feat" style="--c:{f.accent};animation-delay:{i * 0.06:.2f}s">'
        f'<div class="e">{f.emoji}</div><h4>{escape(f.title)}</h4><p>{escape(f.tagline)}</p>'
        f'<div class="tag"><span>{f.category.upper()}</span><span>T={f.temperature} · {f.version}</span></div></div>'
        for i, f in enumerate(features))
    html(f'<div class="cb-grid">{cards}</div>')


def flow(steps: list[tuple[str, str, str]]) -> None:
    colors = ["#C6FF3D", "#3DF5FF", "#9D7BFF", "#FF3DAE", "#FFB13D", "#3DFF9E"]
    cards = "".join(
        f'<div class="cb-card cb-step cb-tilt" style="--c:{colors[i % 6]}"><div class="n">STEP 0{i + 1}</div>'
        f'<b>{t}</b><small>{d}</small><div class="bar" style="animation-delay:{i * .3}s"></div></div>'
        for i, (t, d, _) in enumerate(steps))
    html(f'<div class="cb-flow">{cards}</div>')


def feature_header(f: Feature, temperature: float, top_p: float, top_k: int, live: bool) -> None:
    mode = "GEMINI LIVE" if live else "DEMO ENGINE"
    html(f'<div class="cb-card cb-beam cb-fhead" style="--c:{f.accent}"><div class="e">{f.emoji}</div><div>'
         f'<h3>{escape(f.title)}</h3><p>{escape(f.tagline)}</p><div class="cb-chips">'
         f'<span class="cb-chip hot" style="--c:{f.accent}">{f.category}</span>'
         f'<span class="cb-chip">temperature {temperature}</span><span class="cb-chip">top_p {top_p}</span>'
         f'<span class="cb-chip">top_k {top_k}</span><span class="cb-chip">prompt {f.version}</span>'
         f'<span class="cb-chip">{mode}</span></div></div></div>')


def loader(text: str = "COACHBOT IS DRAWING UP YOUR PLAN") -> str:
    return f'<div class="cb-card cb-loader"><div class="rings"><i></i><i></i><i></i></div><span>{text}</span></div>'


def blocked(message: str, kind: str) -> None:
    icon, title = ("🚑", "Please see a professional first") if kind == "red_flag" else ("🛑", "CoachBot can't help with that")
    html(f'<div class="cb-card cb-block"><div style="font-size:3rem">{icon}</div><h3>{title}</h3>'
         f'<p style="color:#E8C9D3;max-width:620px;margin:auto">{escape(message)}</p>'
         '<p style="color:#8B97B8;margin-top:.8rem;font-size:.85rem">If it feels urgent, contact a parent, coach, school nurse or local emergency number.</p></div>')


def plan(plan: CoachPlan, feature: Feature, status: str) -> None:
    badge = '<span class="cb-status live">● GEMINI LIVE</span>' if status == "ok" else '<span class="cb-status demo">● DEMO ENGINE</span>'
    html(f'<div class="cb-card cb-beam cb-result-hero" style="--c:{feature.accent}">{badge}'
         f'<h2>{escape(plan.headline)}</h2><p>{escape(plan.summary)}</p></div>')
    palette = [feature.accent, "#3DF5FF", "#FF3DAE", "#9D7BFF", "#FFB13D", "#3DFF9E"]
    secs = "".join(
        f'<div class="cb-card cb-tilt cb-sec" style="--c:{palette[i % 6]};animation-delay:{.1 + i * .08:.2f}s">'
        f'<h4><span>{escape(s.icon)}</span>{escape(s.title)}</h4><ul>'
        + "".join(f"<li>{escape(item)}</li>" for item in s.items) + "</ul></div>"
        for i, s in enumerate(plan.sections))
    html(f'<div class="cb-secs">{secs}</div>')
    if plan.coach_message:
        html(f'<div class="cb-card cb-coach"><div class="av"></div><q>{escape(plan.coach_message)}</q></div>')


def safety_notes(notes: list[str]) -> None:
    if notes:
        items = "".join(f"<li>{escape(n)}</li>" for n in notes)
        html(f'<div class="cb-card cb-safety"><b>🛡️ SAFETY FIRST</b><ul>{items}</ul></div>')


def code(text: str) -> None:
    html(f'<div class="cb-code">{escape(text)}</div>')


def versions(f: Feature) -> None:
    rows = "".join(f'<div class="cb-ver"><b>{v}</b><span>{escape(c)}</span></div>' for v, c in f.changelog)
    html(f'<div class="cb-card" style="--c:{f.accent};padding:14px 20px"><b style="font-family:Unbounded">{f.emoji} {escape(f.title)}</b>'
         f'<span class="cb-chip" style="float:right">live: {f.version}</span>{rows}</div>')


def category_color(category: str) -> str:
    return CATEGORY_COLORS.get(category, "#C6FF3D")
