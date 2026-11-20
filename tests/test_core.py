"""Offline tests: run with `python -m pytest -q` (no API key needed)."""

import json
import string

import pytest

from coachbot import charts, safety
from coachbot.features import FEATURES
from coachbot.gemini_client import CoachEngine, Params
from coachbot.prompts import build_prompt, system_instruction
from coachbot.schema import CoachPlan, parse_plan, plan_to_markdown

PROFILE = dict(name="Asha", age=14, gender="Female", sport="Cricket", position="Fast bowler", experience="Developing",
               injuries=["Knee strain"], injury_notes="", intensity="Moderate", styles=["Bodyweight"],
               equipment="Basic (ball, cones, bands)", diet="Vegetarian", calories=2200, allergies="peanuts",
               goal="Build stamina", tone="Hype Coach", language="English")


@pytest.fixture(autouse=True)
def _tmp_log(tmp_path, monkeypatch):
    monkeypatch.setattr("coachbot.logger.config.LOG_FILE", tmp_path / "log.jsonl")
    import coachbot.logger as lg
    monkeypatch.setattr(lg.log_event, "__defaults__", (tmp_path / "log.jsonl",))


def test_at_least_ten_unique_features():
    assert len(FEATURES) >= 10
    assert len({f.id for f in FEATURES}) == len(FEATURES)


@pytest.mark.parametrize("feature", FEATURES, ids=lambda f: f.id)
def test_template_slots_are_filled(feature):
    extras = {x.key: x.default for x in feature.extras}
    prompt = build_prompt(feature, PROFILE, extras, ["constraint"])
    leftover = [name for _, name, _, _ in string.Formatter().parse(prompt) if name]
    assert not leftover
    assert "Fast bowler" in prompt and "HARD CONSTRAINTS" in prompt


@pytest.mark.parametrize("feature", FEATURES, ids=lambda f: f.id)
def test_demo_engine_returns_valid_plan(feature):
    r = CoachEngine(None).generate(feature, PROFILE, {x.key: x.default for x in feature.extras}, Params.for_feature(feature))
    assert r.status == "demo" and r.plan.sections
    if feature.wants_schedule:
        assert len(r.plan.weekly_plan) == 7
        charts.weekly_load(r.plan), charts.load_landscape(r.plan)
    if feature.wants_macros:
        assert r.plan.macros.calories > 0
    charts.focus_radar(r.plan)
    assert plan_to_markdown(r.plan).startswith("# ")


def test_safety_temperatures_are_conservative():
    by_id = {f.id: f for f in FEATURES}
    assert by_id["injury_recovery"].temperature <= 0.3
    assert by_id["mobility_rehab"].temperature <= 0.3
    assert by_id["visualization"].temperature >= 0.7


@pytest.mark.parametrize("text", ["I have chest pain when running", "I hit my head yesterday and feel dizzy after the fall",
                                  "I can't put weight on my ankle"])
def test_red_flags_block(text):
    s = safety.screen_input(PROFILE, text)
    assert not s.allowed and s.kind == "red_flag"


@pytest.mark.parametrize("text", ["best steroids for teens", "how do I lose 5 kg in a week", "should I play through the pain"])
def test_unsafe_requests_blocked(text):
    s = safety.screen_input(PROFILE, text)
    assert not s.allowed and s.kind == "blocked"


def test_injury_and_age_constraints():
    young = {**PROFILE, "age": 11, "injuries": ["Ankle sprain", "Knee strain", "Previous concussion"]}
    s = safety.screen_input(young, "")
    joined = " ".join(s.constraints)
    assert "Under 13" in joined and "heading" in joined and "Multiple injuries" in joined
    assert s.warnings


def test_output_screen_flags_unsafe_terms():
    assert safety.screen_output("Try a fat burner and no pain no gain") == ["fat burner", "no pain no gain"]


def test_parse_plan_handles_code_fences():
    plan = CoachPlan(headline="H", summary="S")
    raw = "```json\n" + plan.model_dump_json() + "\n```"
    assert parse_plan(raw).headline == "H"
    assert parse_plan("Sure! " + json.dumps(plan.model_dump()) + " Good luck").summary == "S"


def test_system_instruction_uses_tone_and_language():
    s = system_instruction({**PROFILE, "tone": "Calm Mentor", "language": "Tamil"})
    assert "Calm Mentor" in s and "Respond in Tamil" in s
