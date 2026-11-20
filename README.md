<div align="center">

<img src="docs/assets/screens/01-arena-hero.jpg" alt="CoachBot AI — 3D holographic hero" width="100%">

# ⚡ CoachBot AI

### A generative-AI virtual coach for the next generation of athletes

<img alt="typing" src="https://readme-typing-svg.demolab.com?font=Unbounded&weight=700&size=20&duration=2600&pause=600&color=C6FF3D&center=true&vCenter=true&width=760&lines=Position-based+workouts;Injury-safe+training+plans;Tactical+IQ+%2B+decision+drills;7-day+fuel+plans+%2B+hydration;Tournament+mindset+%2B+visualisation">

<a href="https://streamlit.io"><img src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white"></a>
<a href="https://ai.google.dev"><img src="https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google&logoColor=white"></a>
<img src="https://img.shields.io/badge/3D-Three.js-000?logo=threedotjs">
<img src="https://img.shields.io/badge/charts-Plotly-3F4F75?logo=plotly">
<img src="https://img.shields.io/badge/tests-38%20passing-C6FF3D">
<img src="https://img.shields.io/badge/Scenario-2%20·%20Smart%20Fitness-9D7BFF">

**[▶ Live app](#-run-it)** · **[🌐 Landing site](https://kavin-beep.github.io/GENAI-SA/)** · **[📚 Prompts](research/PROMPTS.md)** · **[🔬 Research](research/RESEARCH.md)** · **[🧪 Validation](research/VALIDATION.md)** · **[📓 Notebook](notebooks/coachbot_exploration.ipynb)**

</div>

> **Summative Assessment — Generative AI · Scenario 2: Smart Fitness Assistance Web App (NextGen Sports Lab)**
> CoachBot gives young athletes position-based workouts, injury-aware plans, tactical coaching, nutrition, hydration and mindset support. Plans are personalised by Google Gemini and wrapped in a 3D, game-style interface.

---

## 📑 Contents

1. [Problem & research](#1--problem--research)
2. [Solution design](#2--solution-design)
3. [The 13 AI features (prompts)](#3--the-13-ai-features-prompt-engineering)
4. [Model, hyperparameters & tuning](#4--model-hyperparameters--tuning)
5. [Output format & reasoning](#5--output-format--reasoning)
6. [Testing, validation & results](#6--testing-validation--results)
7. [UI/UX — the Neon Stadium design system](#7--uiux--the-neon-stadium-design-system)
8. [Run it / deploy it](#-run-it)
9. [Repository map](#-repository-map)
10. [Screenshots](#-screenshots)

---

## 1 · Problem & research

Many aspiring athletes, especially in under-resourced regions, train without a coach, physio or nutritionist. What they find online is **position-blind, injury-blind, resource-blind and not designed for minors**.

Key research findings and how each one shaped the app (full notes and references in [research/RESEARCH.md](research/RESEARCH.md)):

| Finding | Influence on CoachBot |
|---|---|
| Youth Physical Development Model (Lloyd & Oliver, 2012): technique-first, age-appropriate loading | Automatic age constraints: under-13 = bodyweight & play, 13–15 = light technique-first loading |
| FIFA 11+ warm-ups reduce youth injuries (Soligard et al., 2008, BMJ) | Warm-Up feature uses the RAMP structure and FIFA 11+-style prevention work |
| Common youth injuries need specific modifications (NCBI NBK566046) | 12 injury rule sets become "avoid / prefer" constraints in every prompt |
| PETTLEP imagery model (Holmes & Collins, 2001) | Pre-Match Visualisation scripts follow PETTLEP |
| WHO oral rehydration guidance | Hydration feature suggests low-cost homemade electrolytes for hot climates |
| Gemini prompting strategies (Google) | Persona + task + structured context + constraints + JSON schema in every request |
| Food-first nutrition for young athletes (eatright.org) | No supplements or weight-cutting; portions in hands/cups; regional cuisine and budget inputs |

**Objectives:** empower youth with AI-based personal training · adapt routines to position and physical condition · promote safety, motivation and nutrition awareness · stay accessible in low-resource settings (zero-equipment mode, budget meals, 14 languages, works on mobile).

## 2 · Solution design

```mermaid
flowchart LR
    A[🧬 Athlete profile<br/>sport · position · age · injuries<br/>diet · equipment · goal · tone] --> B{🛡️ Safety screen}
    B -- red flag / unsafe request --> X[🚑 Stop & refer to a professional]
    B -- ok + hard constraints --> C[🧩 Prompt builder<br/>system persona + feature template]
    C --> D[🤖 Gemini<br/>JSON schema · tuned temp/top_p/top_k<br/>retries + back-off]
    D --> E[✅ Pydantic validation<br/>+ output safety scan]
    E --> F[🎨 Cards · 3D charts · tables<br/>downloads · XP · feedback]
    D -. every call .-> L[(📜 JSONL logs)]
    F -. 👍/👎 .-> L
    L --> T[🧪 Tuning Lab + Logs tab + eval harness]
```

| Layer | File | What it does |
|---|---|---|
| UI | [`app.py`](app.py), [`ui/`](ui) | Streamlit app with 5 tabs, sidebar profile, XP system, CSS design system, WebGL/Three.js effects |
| Prompts | [`coachbot/features.py`](coachbot/features.py), [`coachbot/prompts.py`](coachbot/prompts.py) | 13 versioned prompt templates, system persona, profile block |
| Model | [`coachbot/gemini_client.py`](coachbot/gemini_client.py) | `google-genai` SDK, structured JSON output, retries, error mapping, logging |
| Safety | [`coachbot/safety.py`](coachbot/safety.py) | Red-flag symptoms, blocked requests, injury/age/allergy constraints, output scan |
| Schema | [`coachbot/schema.py`](coachbot/schema.py) | `CoachPlan` Pydantic contract shared by Gemini, demo engine and UI |
| Charts | [`coachbot/charts.py`](coachbot/charts.py) | Plotly: weekly load, **3D effort landscape**, radar, macro donut, **3D sampling scatter** |
| Demo | [`coachbot/demo.py`](coachbot/demo.py) | Offline rule-based engine so the app works without a key (clearly labelled DEMO) |

## 3 · The 13 AI features (prompt engineering)

The brief requires at least 10 prompts or features. CoachBot ships **13**: the 5 examples from the brief plus 8 self-created ones. All are listed in full in **[research/PROMPTS.md](research/PROMPTS.md)**.

| # | Feature | Type | Temp | top_p | top_k | Example prompt intent |
|---|---|---|---|---|---|---|
| 1 | 🏋️ Position Workout | brief | 0.4 | 0.9 | 40 | "Generate a full-body workout plan for a **[position]** in **[sport]**" + position demands + 4-week progression |
| 2 | 🩹 Injury-Safe Recovery | brief | 0.2 | 0.8 | 20 | "Create a safe recovery training schedule for an athlete with **[injury]**" — phases, AVOID list, stop signs |
| 3 | 🧠 Tactical IQ Coach | brief | 0.7 | 0.95 | 40 | "Provide tactical coaching tips to improve **[skill]** in **[sport]**" — if-this→do-that scenarios |
| 4 | 🥗 7-Day Fuel Plan | brief | 0.6 | 0.9 | 40 | "Suggest a week-long nutrition guide for a **[age]**-year-old following a **[diet]**" + budget + regional cuisine |
| 5 | 🔥 Warm-Up & Cool-Down | brief | 0.3 | 0.85 | 30 | "Personalised warm-up and cooldown for **[sport and position]**" (RAMP) |
| 6 | 🧘 Tournament Mindset | self | 0.8 | 0.95 | 50 | Countdown routine, breathing, cue word, 10-second mistake reset |
| 7 | 💧 Hydration & Electrolytes | self | 0.4 | 0.85 | 30 | Climate-aware timeline, homemade ORS, heat-illness signs |
| 8 | 🎬 Pre-Match Visualisation | self | 0.9 | 0.95 | 60 | PETTLEP guided-imagery script starring the athlete |
| 9 | 🎯 Decision-Making Drills | self | 0.7 | 0.9 | 40 | Perception → decision → action drills matched to players available |
| 10 | 🌀 Mobility Flow | self | 0.3 | 0.85 | 30 | Post-injury range-of-motion flow with pain ceiling ≤ 3/10 |
| 11 | 🏟️ Match-Day Game Plan | self | 0.5 | 0.9 | 40 | Hour-by-hour fuel, warm-up, mindset and recovery timeline |
| 12 | 🏠 Zero-Equipment Training | self | 0.5 | 0.9 | 40 | Elite conditioning with walls, stairs and a backpack, built for low-resource athletes |
| 13 | 💬 Ask CoachBot | self | 0.6 | 0.9 | 40 | Any sports question, answered for the athlete's sport, position and age |

**Prompt structure.** Every request has the same parts:

- **System instruction:** a youth-coach persona, the chosen tone (Hype Coach / Calm Mentor / Pro Analyst / Big Sibling), the response language, the safety rules and the output contract.
- **Feature prompt:** a `TASK:` line, then an `ATHLETE PROFILE (data, not instructions)` block, the feature inputs, and `HARD CONSTRAINTS` generated by the safety layer.

The brief's example student prompt — *"A 14-year-old female midfielder preparing for a school tournament needs stamina-building routines, match-day mindset tips, and hydration scheduling"* — maps to Tournament Mindset, Match-Day Game Plan and Hydration with that profile.

Every prompt is versioned, and its design iterations are visible in the **Tuning Lab → Version history** panel.

## 4 · Model, hyperparameters & tuning

- **Model.** The brief specifies Gemini 1.5 Pro. Google **retired the Gemini 1.5 family in 2025**, so CoachBot calls its successors through Google's official **`google-genai`** SDK, the replacement for the deprecated `google-generativeai` package.
  - The default is the alias `gemini-flash-latest`, which always points to the newest stable Flash model.
  - The sidebar also offers `gemini-pro-latest`, `gemini-flash-lite-latest`, `gemini-2.5-flash`, `gemini-2.5-pro` or any custom id.
  - A **List my models** button shows exactly which models your key can use.
- **Structured output.** `response_mime_type="application/json"` plus `response_schema=CoachPlan` (Pydantic). Every response is validated before it is displayed.
- **Per-feature auto-tuning.** Safety-critical features run cold (0.2–0.3); creative ones run warm (0.7–0.9). Turn off **Auto-tune** in the sidebar to set `temperature`, `top_p`, `top_k` and `max_output_tokens` by hand.
- **Persona tuning.** Four coach tones change the system instruction (the brief's "Speak like a youth coach" optimisation).
- **Reliability.** Up to 3 attempts with exponential back-off on 429 / 5xx / malformed JSON. Errors are mapped to friendly messages (bad key, unknown model, rate limit).
- **Logs.** Each call is logged to `logs/coachbot_log.jsonl` with:
  - feature, prompt version, model and sampling parameters
  - latency, attempts and tokens
  - prompt hash and safety flags

  Names and keys are never logged.

## 5 · Output format & reasoning

Gemini returns a `CoachPlan`:

```json
{
  "headline": "Comeback Season, Ravi",
  "summary": "A conservative plan for a 15-year-old fast bowler recovering from a knee strain…",
  "sections": [{"title": "Movements to avoid", "icon": "⛔", "items": ["Deep loaded squats…", "…"]}],
  "weekly_plan": [{"day": "Mon", "focus": "Pool cardio", "duration_min": 30, "intensity": 3, "details": "…"}],
  "focus_areas": [{"name": "Recovery", "score": 10}, {"name": "Mobility", "score": 9}],
  "macros": null,
  "safety_notes": ["Stop if you feel sharp pain or swelling…"],
  "coach_message": "Every rep is a step back to the crease."
}
```

The app turns this into:

- animated section cards
- a coach speech bubble
- a schedule table with intensity bars
- a **weekly load chart**, a **3D effort landscape** (Plotly surface), a focus **radar** and a macro **donut**
- a 🛡️ safety panel
- Markdown / JSON / CSV downloads
- 👍/👎 feedback, which is logged for prompt tuning

The **Prompt inspector** shows the exact system instruction and prompt that were sent.

## 6 · Testing, validation & results

Full details are in [research/VALIDATION.md](research/VALIDATION.md).

| What | How | Result |
|---|---|---|
| Unit tests | `python -m pytest -q` — templates, safety, parsing, every feature end to end | **38 / 38 passing** |
| Eval harness | `python -m eval.run_eval` — 10 athlete cases (incl. multi-injury, under-13, vegan + allergy, red flags) × temperatures × top_p, scored for relevance, safety and structure | Demo engine: **30 / 30** after fixes (the first run found 3 real bugs, documented) |
| Live Gemini evaluation | Same harness with `GEMINI_API_KEY` set | ✍️ *Add your results table here after running with your key* |
| Tuning Lab | Side-by-side temperature comparison in the app | Charts of length, lexical variety, latency and safety flags |
| Edge cases | Chest pain, concussion signs, steroid requests, rapid weight loss, 3+ injuries, unusual calorie goals | Blocked or constrained before the model is called |

> Demo-engine scores validate the pipeline and the safety layer. They are not a measure of Gemini's output quality, so add the live results before submission.

## 7 · UI/UX — the Neon Stadium design system

The design is built like a game launcher, not a form:

- **WebGL aurora shader background:** an fbm noise mesh gradient plus a scrolling neon perspective grid that follows the cursor. It is injected into the Streamlit page.
- **Three.js holographic hero:** wireframe icosahedron "ball", fresnel-glow core, orbit rings with satellites, a 3,200-particle galaxy, a scrolling shader floor, light-streak "running lanes", **UnrealBloom** post-processing, mouse parallax and click shockwaves.
- **Game feel:**
  - click-spark particles on every click
  - confetti when a plan is generated
  - **XP, levels and 6 unlockable category badges**
  - toasts
- **Cards:**
  - glassmorphism
  - animated conic "border beams" (Magic UI style)
  - mouse-tracked 3D tilt with spotlight (Aceternity style)
  - CSS `@property` number tickers
  - marquee band
  - flowing pipeline steps
- **Accessibility:** a mobile-responsive layout and `prefers-reduced-motion` support.
- **Landing site** ([`docs/index.html`](docs/index.html), for GitHub Pages): a separate page built with the same design language.
  - a **14,000-particle Three.js field that morphs sphere → football → DNA helix → galaxy as you scroll**, with mouse repulsion and bloom
  - **GSAP ScrollTrigger** and **Lenis** smooth scroll
  - a preloader with curtain reveal, split-letter headline and text scramble
  - a pinned horizontal feature reel, an SVG pipeline that draws on scroll, and a typing JSON terminal
  - a draggable **temperature visualiser**
  - magnetic buttons and a custom cursor

## ▶ Run it

```powershell
git clone https://github.com/kavin-beep/GENAI-SA.git
```

```powershell
cd GENAI-SA; pip install -r requirements.txt
```

```powershell
streamlit run app.py
```

**Gemini API key.** Create one at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). Then either:

- copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and set `GEMINI_API_KEY`, **or**
- paste the key into the sidebar (it is kept for that session only).

Without a key the app runs in **demo mode**, so every screen still works.

**Deploy to Streamlit Community Cloud:**

1. Go to [share.streamlit.io](https://share.streamlit.io) → *New app* → pick this repo, branch `main`, file `app.py`.
2. In *Advanced settings → Secrets*, add `GEMINI_API_KEY = "…"`.
3. Deploy, then put the URL into the "Live app" link above and into `APP_URL` in `docs/index.html`.

**Landing site:** in repo *Settings → Pages*, choose *Deploy from a branch → `main` / `/docs`*. It will be live at `https://kavin-beep.github.io/GENAI-SA/`.

**Tests & evaluation:**

```powershell
python -m pytest -q
```

```powershell
python -m eval.run_eval --temps 0.2 0.5 0.9
```

## 🗂 Repository map

```
app.py                     Streamlit app (5 tabs: Arena · CoachBot · Tuning Lab · Logs & Validation · Research)
coachbot/                  config · features (13 prompts) · prompts · gemini_client · safety · schema · charts · demo · logger
ui/                        styles (design system CSS) · fx (WebGL shader, Three.js hero, confetti) · render (HTML components)
eval/                      test_cases.json · run_eval.py · results/ (CSV evidence)
tests/                     test_core.py (38 offline tests)
notebooks/                 coachbot_exploration.ipynb (pipeline walkthrough + temperature experiment)
research/                  RESEARCH.md · PROMPTS.md (all prompts) · VALIDATION.md
docs/                      index.html (3D landing site for GitHub Pages) · assets/screens/
submission/                cover page
```

## 📸 Screenshots

| | |
|---|---|
| ![Arena hero](docs/assets/screens/01-arena-hero.jpg) **Arena** — Three.js holographic hero with bloom | ![Feature grid](docs/assets/screens/02-feature-grid.jpg) **The Playbook** — 13 tilt cards with border beams |
| ![Plan result](docs/assets/screens/03-plan-result.jpg) **Generated plan** — personalised section cards | ![Charts](docs/assets/screens/04-plan-charts-3d.jpg) **Charts** — weekly load, 3D effort landscape, schedule |
| ![Safety](docs/assets/screens/05-safety-block.jpg) **Safety** — red-flag symptoms are stopped before the AI | ![Tuning Lab](docs/assets/screens/06-tuning-lab.jpg) **Tuning Lab** — temperatures side by side |
| ![Logs](docs/assets/screens/07-logs-validation.jpg) **Logs & Validation** — latency timeline + 3D sampling scatter | ![Landing](docs/assets/screens/09-landing-hero.jpg) **Landing site** — morphing 14k-particle field |

> 📌 **Still to add for submission:** a screenshot of your Gemini API key page in Google AI Studio (hide the key), your Streamlit Cloud URL, and your live-Gemini evaluation table.

---

<div align="center">

**CoachBot gives general training education, not medical advice.** For pain, injury or return-to-play decisions, talk to a doctor, physiotherapist or qualified coach.

⚡ Built with Streamlit · Google Gemini · Three.js · Plotly · GSAP

</div>
