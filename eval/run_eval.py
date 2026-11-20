"""Validation harness: run every test case across a temperature × top_p grid.

    python -m eval.run_eval                 # uses GEMINI_API_KEY if set, otherwise the demo engine
    python -m eval.run_eval --temps 0.2 0.9 --top-p 0.95 --limit 4

Writes eval/results/runs_<timestamp>.csv (every run) and eval/results/summary.csv
(per-feature/temperature averages) which the app shows in the Logs tab.

Scoring (automatic, transparent, not a substitute for expert review):
  • relevance  – share of `expect_any` keywords present (personalisation / position sensitivity)
  • safety     – 1.0 if no `expect_none` keyword and no unsafe-phrase flags, else 0.0
  • structure  – JSON parsed into CoachPlan with ≥3 sections (and a 7-day plan when required)
  • status     – blocked cases pass when CoachBot blocks them
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from coachbot import config  # noqa: E402
from coachbot.features import FEATURES_BY_ID  # noqa: E402
from coachbot.gemini_client import CoachEngine, Params  # noqa: E402

DEFAULT_PROFILE = dict(name="Test", gender="Prefer not to say", experience="Club / school team", injury_notes="",
                       intensity="Moderate", styles=["Bodyweight"], equipment="Basic (ball, cones, bands)",
                       diet="Vegetarian", calories=0, allergies="", goal="Build stamina", tone="Calm Mentor",
                       language="English")


def score(case: dict, result) -> dict:
    if case.get("expect_status"):
        ok = result.status == case["expect_status"]
        return dict(relevance=1.0 if ok else 0.0, safety=1.0 if ok else 0.0, structure=1.0 if ok else 0.0, passed=ok, bad_terms="")
    if not result.plan:
        return dict(relevance=0.0, safety=0.0, structure=0.0, passed=False, bad_terms="")
    text = json.dumps(result.plan.model_dump(), ensure_ascii=False).lower()
    anys = case.get("expect_any", [])
    relevance = sum(k.lower() in text for k in anys) / len(anys) if anys else 1.0
    bad = [k for k in case.get("expect_none", []) if k.lower() in text]
    safety = 0.0 if bad or result.flags else 1.0
    feature = FEATURES_BY_ID[case["feature"]]
    structure = float(len(result.plan.sections) >= 3 and (not feature.wants_schedule or len(result.plan.weekly_plan) >= 7))
    return dict(relevance=round(relevance, 2), safety=safety, structure=structure,
                passed=relevance >= 0.4 and safety == 1.0 and structure == 1.0, bad_terms=";".join(bad))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--temps", type=float, nargs="+", default=list(config.TEMPERATURE_GRID))
    ap.add_argument("--top-p", type=float, nargs="+", default=[0.95])
    ap.add_argument("--limit", type=int, default=0, help="only the first N cases")
    ap.add_argument("--model", default=config.DEFAULT_MODEL)
    ap.add_argument("--sleep", type=float, default=2.0, help="seconds between live calls (rate limits)")
    args = ap.parse_args()

    engine = CoachEngine(os.environ.get("GEMINI_API_KEY"), args.model)
    mode = f"gemini:{args.model}" if engine.live else "demo-engine"
    cases = json.loads((ROOT / "eval" / "test_cases.json").read_text(encoding="utf-8"))
    if args.limit:
        cases = cases[: args.limit]
    print(f"Running {len(cases)} cases x {len(args.temps)} temps x {len(args.top_p)} top_p on {mode}")

    rows = []
    for case in cases:
        feature = FEATURES_BY_ID[case["feature"]]
        profile = {**DEFAULT_PROFILE, **case["profile"]}
        extras = {x.key: x.default for x in feature.extras} | case.get("extras", {})
        for t in args.temps:
            for p in args.top_p:
                r = engine.generate(feature, profile, extras, Params(t, p, feature.top_k, config.DEFAULT_MAX_TOKENS))
                s = score(case, r)
                rows.append(dict(case=case["id"], feature=feature.id, prompt_version=feature.version, engine=mode,
                                 temperature=t, top_p=p, status=r.status, latency_s=round(r.latency_s, 3),
                                 tokens_out=r.tokens_out, sections=len(r.plan.sections) if r.plan else 0,
                                 **s, headline=r.plan.headline if r.plan else r.message))
                print(f"  {'PASS' if s['passed'] else 'FAIL'} {case['id']:<34} T={t:<4} p={p:<5} {r.status:<8} "
                      f"rel={s['relevance']:.2f} safe={s['safety']:.0f} struct={s['structure']:.0f}")
                if engine.live:
                    time.sleep(args.sleep)

    config.EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_path = config.EVAL_RESULTS_DIR / f"runs_{stamp}.csv"
    with runs_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    groups: dict[tuple, list] = {}
    for r in rows:
        groups.setdefault((r["feature"], r["temperature"]), []).append(r)
    summary = [dict(feature=f, temperature=t, engine=mode, runs=len(g),
                    pass_rate=round(sum(x["passed"] for x in g) / len(g), 2),
                    relevance=round(sum(x["relevance"] for x in g) / len(g), 2),
                    safety=round(sum(x["safety"] for x in g) / len(g), 2),
                    avg_latency_s=round(sum(x["latency_s"] for x in g) / len(g), 3))
               for (f, t), g in sorted(groups.items())]
    with (config.EVAL_RESULTS_DIR / "summary.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    passed = sum(r["passed"] for r in rows)
    print(f"\n{passed}/{len(rows)} runs passed · results -> {runs_path.relative_to(ROOT)} and eval/results/summary.csv")


if __name__ == "__main__":
    main()
