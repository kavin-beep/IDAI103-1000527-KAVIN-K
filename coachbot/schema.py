"""Structured output contract shared by Gemini, the demo engine and the UI."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError


class Section(BaseModel):
    title: str = Field(description="Short section heading")
    icon: str = Field(default="⚡", description="One emoji that represents the section")
    items: list[str] = Field(default_factory=list, description="3-7 concrete, actionable bullet points")


class PlanDay(BaseModel):
    day: str = Field(description="Day label, e.g. 'Mon' or 'Day 1'")
    focus: str = Field(description="Main focus of the session")
    duration_min: int = Field(default=0, description="Session length in minutes (0 for rest)")
    intensity: int = Field(default=0, description="Effort on a 0-10 scale (0 = full rest)")
    details: str = Field(default="", description="What to do in one or two sentences")


class FocusArea(BaseModel):
    name: str = Field(description="Athletic quality, e.g. Stamina, Speed, Strength, Mobility, Tactics, Mindset, Recovery")
    score: int = Field(description="How much this plan develops it, 0-10")


class Macros(BaseModel):
    calories: int = Field(default=0, description="Daily calorie target")
    protein_pct: int = Field(default=0)
    carbs_pct: int = Field(default=0)
    fat_pct: int = Field(default=0)


class CoachPlan(BaseModel):
    headline: str = Field(description="Catchy, motivating title for this plan (max 10 words)")
    summary: str = Field(description="2-3 sentence personalised overview mentioning sport, position and goal")
    sections: list[Section] = Field(default_factory=list, description="3-6 themed sections")
    weekly_plan: list[PlanDay] = Field(default_factory=list, description="Optional schedule; empty if not relevant")
    focus_areas: list[FocusArea] = Field(default_factory=list, description="5-7 qualities for a radar chart")
    macros: Macros | None = Field(default=None, description="Only for nutrition features")
    safety_notes: list[str] = Field(default_factory=list, description="Injury-aware cautions and when to stop")
    coach_message: str = Field(default="", description="One motivating sentence in the selected coach tone")


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_plan(raw: str) -> CoachPlan:
    """Parse model text into a CoachPlan, tolerating code fences and stray prose."""
    text = _FENCE.sub("", raw.strip())
    try:
        return CoachPlan.model_validate_json(text)
    except ValidationError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        return CoachPlan.model_validate(json.loads(text[start : end + 1]))


def plan_to_markdown(plan: CoachPlan, title_prefix: str = "") -> str:
    lines = [f"# {title_prefix}{plan.headline}", "", plan.summary, ""]
    for section in plan.sections:
        lines += [f"## {section.icon} {section.title}", *[f"- {item}" for item in section.items], ""]
    if plan.weekly_plan:
        lines += ["## 📅 Schedule", "", "| Day | Focus | Minutes | Intensity | Details |", "|---|---|---|---|---|"]
        lines += [f"| {d.day} | {d.focus} | {d.duration_min} | {d.intensity}/10 | {d.details} |" for d in plan.weekly_plan]
        lines.append("")
    if plan.macros and plan.macros.calories:
        m = plan.macros
        lines += ["## 🍽️ Daily fuel", f"- Calories: {m.calories} kcal",
                  f"- Protein {m.protein_pct}% · Carbs {m.carbs_pct}% · Fat {m.fat_pct}%", ""]
    if plan.safety_notes:
        lines += ["## 🛡️ Safety", *[f"- {n}" for n in plan.safety_notes], ""]
    if plan.coach_message:
        lines += [f"> {plan.coach_message}", ""]
    return "\n".join(lines)
