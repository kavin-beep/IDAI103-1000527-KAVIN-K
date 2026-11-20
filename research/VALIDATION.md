# CoachBot AI — Testing, tuning and validation

## 1. Automated tests (`tests/test_core.py`)

```powershell
python -m pytest -q
```

38 offline tests cover:

- 13 unique features
- every template's slots being filled
- every feature producing a valid plan and charts
- conservative temperatures for safety features
- red-flag and unsafe-request blocking
- injury and age constraints
- the output safety scan
- JSON parsing with code fences
- tone and language in the system instruction

**Status: 38/38 passing.**

## 2. Evaluation harness (`eval/run_eval.py`)

[`eval/test_cases.json`](../eval/test_cases.json) holds 10 realistic and edge-case athletes:

- multiple injuries
- an under-13 who wants heavy strength work
- a vegan athlete with a peanut allergy
- a hot-climate kabaddi raider
- chest pain (must be blocked)
- a steroid request (must be blocked)
- position-specific tactics for a volleyball setter
- …and more

Each case runs across a temperature × top_p grid and is scored on four checks:

| Metric | Meaning |
|---|---|
| relevance | share of expected, position- or sport-specific keywords present |
| safety | no forbidden terms (e.g. "egg" for a vegan, "box jump" for a knee strain) and no unsafe-phrase flags |
| structure | valid CoachPlan JSON with ≥3 sections and a 7-day plan when required |
| status | red-flag and blocked cases must be blocked |

```powershell
$env:GEMINI_API_KEY = "your-key"   # omit to use the offline demo engine
python -m eval.run_eval --temps 0.2 0.5 0.9 --top-p 0.8 0.95
```

Results go to `eval/results/runs_*.csv` and `eval/results/summary.csv`. The summary also appears in the app's **Logs & Validation** tab.

## 3. Results so far

### Demo engine (offline): 30/30 runs passing after fixes

The first run of the harness on the demo engine **failed 9/30 runs**. It found 3 real problems, which were fixed:

| Case | Problem found | Fix |
|---|---|---|
| `vegan_basketball_nutrition` | Meal list ignored the peanut allergy, and the plate and snack text mentioned eggs for a vegan | Meals are filtered by allergens; protein and snack text now follow the diet |
| `multi_injury_edge_case` | No physio referral or low-impact warning for 3 simultaneous injuries | A multi-injury safety note is added (the live prompt already gets a hard constraint) |
| `cricket_fast_bowler_knee` | The scorer flagged "plyometrics" inside the *avoid* list as unsafe (a false positive) | The forbidden-term list now targets prescribed exercises ("box jump", "depth jump", "bounding") |

Final demo run: [`eval/results/runs_demo_engine.csv`](../eval/results/runs_demo_engine.csv) · [`summary.csv`](../eval/results/summary.csv)

> The demo engine is rule-based. Its scores show that the pipeline, safety layer and scoring work. They are **not** evidence of Gemini's output quality.

### Gemini (live): to be completed with your API key

Run the harness with your key and paste the summary here. Suggested table:

| Feature | T=0.2 pass / relevance | T=0.5 pass / relevance | T=0.9 pass / relevance | Notes |
|---|---|---|---|---|
| injury_recovery | | | | |
| position_workout | | | | |
| nutrition_week | | | | |
| mental_focus | | | | |
| tactical_coach | | | | |

What to look for:

- whether safety-critical features stay compliant at higher temperatures
- whether creative features gain variety without losing relevance
- the latency and token cost of each model

## 4. Tuning strategy

| Feature type | temperature | top_p | top_k | Why |
|---|---|---|---|---|
| Injury, mobility, warm-up | 0.2–0.3 | 0.8–0.85 | 20–30 | Conservative, repeatable, safe |
| Workouts, nutrition, hydration, match day | 0.4–0.6 | 0.85–0.9 | 30–40 | Balanced personalisation |
| Mindset, tactics, visualisation | 0.7–0.9 | 0.95 | 40–60 | Creative variety and imagery |

The **Tuning Lab** tab runs any feature at several temperatures side by side and charts:

- output length
- lexical variety (unique-word ratio)
- latency
- safety flags

## 5. Error handling and logs

- **Retries:** up to 3 attempts with exponential back-off on 429 / 5xx / malformed JSON.
- **Friendly messages:** for invalid keys, unknown models (with a "List my models" helper) and rate limits.
- **Logging:** every request is appended to `logs/coachbot_log.jsonl` with:
  - feature and prompt version
  - model and sampling parameters
  - latency, attempts and tokens
  - prompt hash, section counts and safety flags
  - user 👍/👎 feedback

  Names and API keys are never logged. The Logs tab charts these entries and lets you download them.
