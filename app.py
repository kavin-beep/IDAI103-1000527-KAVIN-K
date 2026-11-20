"""CoachBot AI — a generative-AI virtual coach for young athletes (Scenario 2).

Run locally:   streamlit run app.py
Gemini key:    .streamlit/secrets.toml  →  GEMINI_API_KEY = "..."
Without a key the app runs on the offline demo engine so every screen still works.
"""

from __future__ import annotations

import json
import os
import re

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from coachbot import charts, config
from coachbot.features import FEATURES, FEATURES_BY_ID, Feature
from coachbot.gemini_client import CoachEngine, Params, Result
from coachbot.logger import log_event, read_logs
from coachbot.schema import plan_to_markdown
from ui import fx, render
from ui.styles import CSS

st.set_page_config(page_title="CoachBot AI · Virtual Coach", page_icon="⚡", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)
components.html(fx.GLOBAL_FX, height=0)

ss = st.session_state
ss.setdefault("xp", 0)
ss.setdefault("unlocked", set())
ss.setdefault("result", None)
ss.setdefault("result_feature", None)
ss.setdefault("lab", [])
ss.setdefault("nonce", 0)
ss.setdefault("celebrate", False)


def secret_key() -> str:
    try:
        return st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("gemini", {}).get("api_key", "")
    except Exception:  # no secrets.toml
        return os.environ.get("GEMINI_API_KEY", "")


# ═════════════════════════════ SIDEBAR: athlete profile ═════════════════════════════
with st.sidebar:
    render.logo()
    xp_slot = st.empty()  # filled at the end of the run so freshly earned XP shows immediately

    st.markdown("### 🧬 Athlete profile")
    name = st.text_input("Name / nickname", "Asha", max_chars=40)
    c1, c2 = st.columns(2)
    age = c1.number_input("Age", 8, 21, 14)
    gender = c2.selectbox("Gender", ("Female", "Male", "Non-binary", "Prefer not to say"))
    sport = st.selectbox("Sport", list(config.SPORT_POSITIONS))
    position = st.selectbox("Position", config.SPORT_POSITIONS[sport] + ["Other"])
    if position == "Other":
        position = st.text_input("Your position", "Utility player", max_chars=40)
    experience = st.select_slider("Experience", config.EXPERIENCE_LEVELS, value="Club / school team")

    st.markdown("### 🩹 Injuries & risk zones")
    injuries = st.multiselect("Injury history", config.INJURY_OPTIONS, default=["Knee strain"])
    injury_notes = st.text_input("Anything else? (optional)", "", max_chars=200,
                                 placeholder="e.g. right knee, 6 weeks ago")

    st.markdown("### 🏃 Training")
    intensity = st.select_slider("Preferred intensity", config.INTENSITY_LEVELS, value="Moderate")
    styles = st.multiselect("Training styles", config.TRAINING_STYLES, default=["Bodyweight", "Field drills"])
    equipment = st.selectbox("Equipment access", config.EQUIPMENT_LEVELS, index=1)
    goal = st.selectbox("Main goal", config.GOALS)

    st.markdown("### 🥗 Nutrition")
    diet = st.selectbox("Diet", config.DIET_TYPES, index=1)
    calories = st.number_input("Daily calorie goal (0 = let coach decide)", 0, 5000, 2200, step=100)
    allergies = st.text_input("Allergies", "", max_chars=120, placeholder="e.g. peanuts, lactose")

    st.markdown("### 🎙️ Coach style")
    tone = st.selectbox("Coach persona", list(config.COACH_TONES))
    language = st.selectbox("Response language", config.LANGUAGES)

    st.markdown("### 🤖 Model & tuning")
    key = secret_key()
    if not key:
        key = st.text_input("Gemini API key (kept for this session only)", type="password",
                            help="Get one free at aistudio.google.com/app/apikey. Leave empty to use demo mode.")
    model = st.selectbox("Gemini model", config.MODEL_OPTIONS + ("Custom…",))
    if model == "Custom…":
        model = st.text_input("Model id", "gemini-2.5-flash")
    auto = st.toggle("Auto-tune per feature", True, help="Use each feature's tested temperature / top_p / top_k.")
    manual = Params(
        temperature=st.slider("temperature", 0.0, 2.0, config.DEFAULT_TEMPERATURE, 0.05, disabled=auto),
        top_p=st.slider("top_p", 0.1, 1.0, config.DEFAULT_TOP_P, 0.05, disabled=auto),
        top_k=st.slider("top_k", 1, 100, config.DEFAULT_TOP_K, disabled=auto),
        max_tokens=st.slider("max output tokens", 512, 8192, config.DEFAULT_MAX_TOKENS, 256),
    )

engine = CoachEngine(key, model)
with st.sidebar:
    if engine.live:
        st.success(f"Gemini connected · {model}", icon="🟢")
        if st.button("List my models", width="stretch"):
            try:
                st.code("\n".join(engine.list_models()) or "No Gemini models returned.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not list models: {type(exc).__name__}")
    else:
        st.info("Demo mode — add a Gemini key for live AI.", icon="🧪")
    st.caption(config.SAFETY_DISCLAIMER)

profile = dict(name=name, age=int(age), gender=gender, sport=sport, position=position, experience=experience,
               injuries=injuries, injury_notes=injury_notes, intensity=intensity, styles=styles,
               equipment=equipment, goal=goal, diet=diet, calories=int(calories), allergies=allergies,
               tone=tone, language=language)


def params_for(feature: Feature) -> Params:
    return Params.for_feature(feature, manual.max_tokens) if auto else manual


def award(feature: Feature) -> None:
    gained = 25 if feature.category not in ss.unlocked else 10
    ss.xp += gained
    if feature.category not in ss.unlocked:
        ss.unlocked.add(feature.category)
        st.toast(f"Badge unlocked: {feature.category} {feature.emoji}", icon="🏆")
    st.toast(f"+{gained} XP", icon="⚡")


def extras_form(feature: Feature) -> dict:
    values: dict = {}
    if not feature.extras:
        return values
    cols = st.columns(min(3, len(feature.extras)))
    for i, x in enumerate(feature.extras):
        col, k = cols[i % len(cols)], f"x_{feature.id}_{x.key}"
        if x.kind == "slider":
            values[x.key] = col.slider(x.label, x.options[0], x.options[1], x.default, key=k)
        elif x.kind == "select":
            values[x.key] = col.selectbox(x.label, x.options, index=x.options.index(x.default), key=k)
        elif x.kind == "area":
            values[x.key] = st.text_area(x.label, x.default, max_chars=600, key=k)
        else:
            values[x.key] = col.text_input(x.label, x.default, max_chars=160, key=k)
    return values


def show_result(result: Result, feature: Feature, key_prefix: str = "main") -> None:
    for w in result.warnings:
        st.warning(w, icon="⚠️")
    if result.status == "blocked":
        render.blocked(result.message, result.flags[0] if result.flags else "")
        return
    if result.status == "error":
        st.error(f"{result.message}  (after {result.attempts} attempt(s), {result.latency_s:.1f}s)", icon="🚨")
        if result.raw:
            with st.expander("Raw model output"):
                st.code(result.raw[:4000])
        return
    plan = result.plan
    render.plan(plan, feature, result.status)

    if plan.weekly_plan:
        c1, c2 = st.columns([1.15, 1])
        c1.plotly_chart(charts.weekly_load(plan), theme=None, key=f"{key_prefix}_load")
        c2.plotly_chart(charts.load_landscape(plan), theme=None, key=f"{key_prefix}_3d")
        df = pd.DataFrame([d.model_dump() for d in plan.weekly_plan]).rename(columns={
            "day": "Day", "focus": "Focus", "duration_min": "Minutes", "intensity": "Intensity", "details": "Details"})
        st.dataframe(df, hide_index=True, width="stretch", column_config={
            "Intensity": st.column_config.ProgressColumn("Intensity", min_value=0, max_value=10, format="%d/10"),
            "Minutes": st.column_config.NumberColumn("Minutes", format="%d min")})
    c1, c2 = st.columns(2)
    if plan.focus_areas:
        c1.plotly_chart(charts.focus_radar(plan), theme=None, key=f"{key_prefix}_radar")
    if plan.macros and plan.macros.calories:
        c2.plotly_chart(charts.macro_donut(plan), theme=None, key=f"{key_prefix}_macro")
    else:
        with c2:
            render.safety_notes(plan.safety_notes)
    if plan.macros and plan.macros.calories:
        render.safety_notes(plan.safety_notes)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Latency", f"{result.latency_s:.2f}s")
    m2.metric("Tokens in / out", f"{result.tokens_in} / {result.tokens_out}" if result.tokens_in else "—")
    m3.metric("Attempts", result.attempts)
    m4.metric("Safety flags", len(result.flags))

    d1, d2, d3, d4 = st.columns([1, 1, 1, 1.3])
    slug = re.sub(r"[^a-z0-9]+", "-", feature.title.lower())
    d1.download_button("⬇ Markdown", plan_to_markdown(plan), f"coachbot-{slug}.md", "text/markdown",
                       width="stretch", key=f"{key_prefix}_md")
    d2.download_button("⬇ JSON", plan.model_dump_json(indent=2), f"coachbot-{slug}.json", "application/json",
                       width="stretch", key=f"{key_prefix}_json")
    if plan.weekly_plan:
        csv = pd.DataFrame([d.model_dump() for d in plan.weekly_plan]).to_csv(index=False)
        d3.download_button("⬇ Schedule CSV", csv, f"coachbot-{slug}.csv", "text/csv", width="stretch",
                           key=f"{key_prefix}_csv")
    with d4:
        rating = st.feedback("thumbs", key=f"{key_prefix}_fb_{ss.nonce}")
        if rating is not None and not ss.get(f"rated_{ss.nonce}"):
            ss[f"rated_{ss.nonce}"] = True
            log_event({"type": "feedback", "feature": feature.id, "prompt_version": feature.version,
                       "rating": int(rating), "status": result.status})
            st.toast("Thanks! Feedback logged for prompt tuning.", icon="📝")
    with st.expander("🔍 Prompt inspector — exactly what was sent to the model"):
        st.markdown("**System instruction**")
        render.code(result.system)
        st.markdown("**User prompt**")
        render.code(result.prompt)


# ═════════════════════════════ MAIN TABS ═════════════════════════════
tab_arena, tab_coach, tab_lab, tab_logs, tab_research = st.tabs(
    ["🏟️  Arena", "⚡  CoachBot", "🧪  Tuning Lab", "📊  Logs & Validation", "📚  Research"])

positions_total = sum(len(v) for v in config.SPORT_POSITIONS.values())

# ── ARENA ────────────────────────────────────────────────────────────────────
with tab_arena:
    components.html(fx.hero_html(
        "A virtual coach in your pocket. Position-based workouts, injury-safe training, tactics, "
        "nutrition and mindset — personalised by Google Gemini for every young athlete, everywhere.",
        (len(FEATURES), len(config.SPORT_POSITIONS), positions_total)), height=620)
    render.marquee(["POSITION WORKOUTS", "INJURY-SAFE", "TACTICAL IQ", "7-DAY FUEL", "MINDSET",
                    "HYDRATION", "VISUALISATION", "ZERO EQUIPMENT", "MATCH DAY"])
    render.stats([(len(FEATURES), "AI coaching features", "#C6FF3D"), (len(config.SPORT_POSITIONS), "sports", "#3DF5FF"),
                  (positions_total, "positions mapped", "#FF3DAE"), (len(config.INJURY_OPTIONS), "injury rules", "#FFB13D"),
                  (len(config.LANGUAGES), "languages", "#9D7BFF")])
    render.heading("THE PLAYBOOK", "Thirteen ways to level up.",
                   "Every card is a hand-engineered, versioned Gemini prompt with its own tuned temperature. "
                   "Hover them — they react.")
    render.feature_grid()
    render.heading("UNDER THE HOOD", "From profile to plan in seconds.")
    render.flow([("Profile", "Sport, position, age, injuries, diet, goal", ""),
                 ("Safety screen", "Red-flag symptoms & unsafe requests stop here", ""),
                 ("Prompt build", "Persona + task + profile + hard constraints", ""),
                 ("Gemini", "JSON schema output, tuned sampling, retries", ""),
                 ("Validate", "Pydantic parsing + output safety scan + logs", ""),
                 ("Visualise", "Cards, 3D charts, downloads, feedback", "")])

# ── COACHBOT ─────────────────────────────────────────────────────────────────
with tab_coach:
    render.heading("VIRTUAL COACH", f"Let's train, {name or 'champ'}.",
                   f"{position} · {sport} · age {age} · goal: {goal.lower()}")
    fid = st.pills("Choose a coaching feature", [f.id for f in FEATURES], default=FEATURES[0].id,
                   format_func=lambda i: f"{FEATURES_BY_ID[i].emoji} {FEATURES_BY_ID[i].title}", key="feature_pick")
    feature = FEATURES_BY_ID[fid or FEATURES[0].id]
    p = params_for(feature)
    render.feature_header(feature, p.temperature, p.top_p, p.top_k, engine.live)
    extras = extras_form(feature)
    notes = st.text_input("Extra context for the coach (optional)", "", max_chars=300,
                          placeholder="e.g. school exams next week, only free after 6 PM", key=f"notes_{feature.id}")
    go = st.button(f"{feature.emoji}  Generate {feature.title}", type="primary", width="stretch")
    slot = st.empty()
    if go:
        slot.markdown(render.loader(), unsafe_allow_html=True)
        res = engine.generate(feature, {**profile, "notes": notes}, extras, p)
        slot.empty()
        ss.result, ss.result_feature = res, feature.id
        ss.nonce += 1
        if res.status in ("ok", "demo"):
            award(feature)
            ss.celebrate = True
    if ss.result and ss.result_feature == feature.id:
        show_result(ss.result, feature)
        if ss.celebrate:
            components.html(fx.confetti_js(ss.nonce), height=0)
            ss.celebrate = False
    elif ss.result:
        st.caption(f"Your last plan was for **{FEATURES_BY_ID[ss.result_feature].title}** — select it above to view it again.")

# ── TUNING LAB ───────────────────────────────────────────────────────────────
with tab_lab:
    render.heading("TUNING LAB", "Same prompt. Different temperatures.",
                   "Run one feature at several sampling settings side by side to see how creativity, length and "
                   "safety change. Every run is logged for the validation report.")
    c1, c2, c3 = st.columns([1.4, 1, 1])
    lab_fid = c1.selectbox("Feature", [f.id for f in FEATURES], index=1,
                           format_func=lambda i: f"{FEATURES_BY_ID[i].emoji} {FEATURES_BY_ID[i].title}")
    temps = c2.multiselect("Temperatures", [0.0, 0.2, 0.5, 0.7, 0.9, 1.2], default=list(config.TEMPERATURE_GRID))
    top_p = c3.select_slider("top_p", [0.5, 0.8, 0.9, 0.95, 1.0], value=0.95)
    lab_feature = FEATURES_BY_ID[lab_fid]
    if st.button("🧪  Run comparison", type="primary", width="stretch", disabled=not temps):
        runs = []
        bar = st.progress(0.0, "Running…")
        lab_extras = {x.key: x.default for x in lab_feature.extras}
        for i, t in enumerate(sorted(temps)):
            r = engine.generate(lab_feature, profile, lab_extras, Params(t, top_p, lab_feature.top_k, manual.max_tokens))
            runs.append((t, r))
            bar.progress((i + 1) / len(temps), f"temperature {t} done")
        bar.empty()
        ss.lab = [(lab_fid, t, r) for t, r in runs]
    if ss.lab:
        rows = []
        for fid_, t, r in ss.lab:
            text = " ".join([r.plan.summary] + [i for s in r.plan.sections for i in s.items]) if r.plan else ""
            words = re.findall(r"[a-zA-Z']+", text.lower())
            rows.append({"label": f"T={t}", "temperature": t, "status": r.status, "latency_s": round(r.latency_s, 3),
                         "words": len(words), "unique_ratio": round(len(set(words)) / max(1, len(words)), 2),
                         "sections": len(r.plan.sections) if r.plan else 0, "safety_flags": len(r.flags)})
        g1, g2, g3 = st.columns(3)
        g1.plotly_chart(charts.compare_bars(rows, "words", "📝 Output length (words)"), theme=None, key="lab_words")
        g2.plotly_chart(charts.compare_bars(rows, "unique_ratio", "🎨 Lexical variety"), theme=None, key="lab_var")
        g3.plotly_chart(charts.compare_bars(rows, "latency_s", "⏱️ Latency (s)"), theme=None, key="lab_lat")
        st.dataframe(pd.DataFrame(rows).drop(columns="label"), hide_index=True, width="stretch")
        cols = st.columns(len(ss.lab))
        for col, (fid_, t, r) in zip(cols, ss.lab):
            with col:
                st.markdown(f"#### 🌡️ T = {t}")
                if r.plan:
                    st.markdown(f"**{r.plan.headline}**")
                    st.caption(r.plan.summary)
                    for s in r.plan.sections[:3]:
                        with st.expander(f"{s.icon} {s.title}"):
                            st.markdown("\n".join(f"- {i}" for i in s.items))
                else:
                    st.warning(r.message)
    st.divider()
    render.heading("PROMPT ENGINEERING", "Version history.",
                   "Design-review iterations for each prompt — the live version is what the app sends.")
    v1, v2 = st.columns(2)
    for i, f in enumerate(FEATURES):
        with (v1 if i % 2 == 0 else v2):
            render.versions(f)
    with st.expander("See the system instruction and a rendered prompt for your current profile"):
        from coachbot.prompts import build_prompt, system_instruction
        from coachbot.safety import screen_input
        render.code(system_instruction(profile))
        scr = screen_input(profile, "")
        render.code(build_prompt(lab_feature, profile, {x.key: x.default for x in lab_feature.extras}, scr.constraints))

# ── LOGS & VALIDATION ────────────────────────────────────────────────────────
with tab_logs:
    render.heading("EVIDENCE", "Logs & validation.",
                   "Every request is logged (no names or keys) with its parameters, latency, tokens and safety flags.")
    logs = read_logs()
    gen = [r for r in logs if r.get("type") != "feedback"]
    fb = [r for r in logs if r.get("type") == "feedback"]
    if gen:
        df = pd.DataFrame(gen)
        df["ts"] = pd.to_datetime(df["ts"])
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Requests", len(df))
        k2.metric("Success", f"{(df['status'].isin(['ok', 'demo'])).mean() * 100:.0f}%")
        k3.metric("Avg latency", f"{df['latency_s'].mean():.2f}s")
        k4.metric("Blocked (safety)", int((df["status"] == "blocked").sum()))
        k5.metric("👍 rate", f"{(sum(r['rating'] for r in fb) / len(fb) * 100):.0f}%" if fb else "—")
        c1, c2 = st.columns(2)
        c1.plotly_chart(charts.log_timeline(df), theme=None, key="log_tl")
        c2.plotly_chart(charts.temperature_scatter3d(df.fillna({"top_p": 0.9})), theme=None, key="log_3d")
        st.dataframe(df.sort_values("ts", ascending=False), hide_index=True, width="stretch")
        st.download_button("⬇ Download log (JSONL)", "\n".join(json.dumps(r) for r in logs),
                           "coachbot_log.jsonl", "application/json")
    else:
        st.info("No requests yet — generate a plan in the CoachBot tab and it will appear here.", icon="📭")
    summary = config.EVAL_RESULTS_DIR / "summary.csv"
    if summary.exists():
        st.markdown("#### 🧾 Offline evaluation (eval/run_eval.py)")
        st.dataframe(pd.read_csv(summary), hide_index=True, width="stretch")

# ── RESEARCH ─────────────────────────────────────────────────────────────────
with tab_research:
    render.heading("WHY COACHBOT", "Coaching shouldn't depend on your postcode.",
                   "The research and design decisions behind the app.")
    r1, r2 = st.columns(2)
    with r1:
        render.html("""<div class="cb-card cb-beam" style="--c:#C6FF3D"><h4>🎯 The problem</h4><ul class="cb-r">
<li>Many young athletes — especially in under-resourced regions — have no access to qualified coaches, physios or nutritionists.</li>
<li>Generic online workouts ignore position demands: a goalkeeper, a fast bowler and a point guard need very different training.</li>
<li>Youth injuries (ankle sprains, knee and growth-plate issues, hamstring strains) often come from overload and poor return-to-play.</li>
</ul></div>""")
        render.html("""<div class="cb-card cb-beam" style="--c:#3DF5FF;margin-top:14px"><h4>🔬 Research that shaped it</h4><ul class="cb-r">
<li><b>Long-Term Athlete Development:</b> technique-first, age-appropriate loading — enforced as hard constraints for under-13 and 13–15.</li>
<li><b>RAMP warm-ups & FIFA 11+:</b> structured warm-ups reduce injury risk — built into the warm-up feature.</li>
<li><b>PETTLEP imagery model:</b> evidence-based visualisation — used in the pre-match script feature.</li>
<li><b>WHO oral rehydration guidance:</b> low-cost homemade electrolyte options for hot climates.</li>
<li><b>Gemini prompting strategies:</b> persona, clear task, structured context, output schema and constraints.</li>
</ul></div>""")
    with r2:
        render.html("""<div class="cb-card cb-beam" style="--c:#FF3DAE"><h4>🛡️ Safety by design</h4><ul class="cb-r">
<li>Red-flag symptoms (chest pain, concussion signs, fainting…) are blocked before any model call and routed to professional help.</li>
<li>Requests for steroids, starvation diets or weight-cutting are refused.</li>
<li>Each listed injury adds specific movements to avoid; output is scanned for unsafe phrases.</li>
<li>Low temperatures (0.2–0.3) for injury, mobility and warm-up plans; higher (0.7–0.9) only for creative mindset and tactics.</li>
</ul></div>""")
        render.html("""<div class="cb-card cb-beam" style="--c:#FFB13D;margin-top:14px"><h4>📚 Key references</h4><ul class="cb-r">
<li>Google — <i>Gemini API prompting strategies</i>, ai.google.dev</li>
<li>Lloyd & Oliver (2012) — <i>The Youth Physical Development Model</i>, Strength & Cond. Journal</li>
<li>Soligard et al. (2008) — <i>FIFA 11+ injury prevention in youth football</i>, BMJ</li>
<li>Holmes & Collins (2001) — <i>The PETTLEP approach to motor imagery</i>, J. Applied Sport Psychology</li>
<li>NCBI Bookshelf NBK566046 — <i>sports injuries in youth</i>; ExRx.net workout library; eatright.org</li>
<li>IJISRT — <i>AI-powered fitness web app</i>; TIJER — <i>AI fitness assistant</i></li>
</ul></div>""")
    render.html("<style>.cb-r{padding-left:1.1rem;margin:.4rem 0 0}.cb-r li{color:#C9D3EE;margin:.45rem 0;font-size:.93rem}"
                ".cb-card h4{margin:0 0 .3rem!important;font-size:1.05rem!important}</style>")

render.html(f'<div class="cb-foot">⚡ COACHBOT AI · NEXTGEN SPORTS LAB · BUILT WITH STREAMLIT + GOOGLE GEMINI<br>'
            f'{config.SAFETY_DISCLAIMER}</div>')

with xp_slot.container():
    render.xp_card(ss.xp, ss.unlocked)
