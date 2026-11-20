"""Offline demo engine.

Lets anyone explore the full UI without a Gemini key. It builds a personalised
CoachPlan from rule-based templates. Higher temperature = more random variety,
mirroring how sampling temperature behaves. Outputs are labelled DEMO in the UI
and are NOT presented as Gemini results.
"""

from __future__ import annotations

import random
import zlib

from coachbot import safety
from coachbot.features import Feature
from coachbot.schema import CoachPlan, FocusArea, Macros, PlanDay, Section

SPORT_DRILLS = {
    "Football (Soccer)": ["10 × 30 m repeated sprints, 30 s walk back", "Rondo 4v1, two-touch, 4 × 3 min",
                          "Wall passes: 100 alternating-foot touches", "Cone weave dribbling, 6 × 20 m",
                          "1v1 defending shadow drill, 5 × 30 s", "Copenhagen plank, 3 × 20 s each side"],
    "Cricket": ["Bowling run-up rhythm drill without ball, 3 × 6", "Medicine-ball / backpack rotational throws, 3 × 8",
                "Shadow batting footwork, 4 × 2 min", "Shuttle runs between wickets, 8 × 2 runs",
                "Single-leg balance with eyes closed, 3 × 30 s", "Band external rotations, 3 × 15"],
    "Basketball": ["Defensive slide ladder, 5 × 20 s", "Form shooting close to the rim, 50 makes",
                   "Two-ball dribbling, 4 × 1 min", "Box jumps or step-ups, 3 × 6",
                   "Suicide sprints (court lines), 6 reps", "Lateral lunges, 3 × 10 each side"],
    "Athletics": ["A-skips and B-skips, 3 × 20 m", "Hill sprints, 8 × 10 s", "Tempo runs, 6 × 100 m at 70 %",
                  "Bounding, 4 × 20 m", "Single-leg Romanian deadlift, 3 × 8", "Ankle hops, 3 × 20"],
}
GENERIC_DRILLS = ["Agility ladder or chalk ladder, 6 patterns × 2", "Squat to calf raise, 3 × 12",
                  "Plank variations, 3 × 30 s", "Split-squat holds, 3 × 20 s each leg",
                  "Skipping rope (or imaginary rope), 5 × 1 min", "Partner reaction ball drops, 4 × 10"]

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
QUALITIES = ("Stamina", "Speed", "Strength", "Agility", "Mobility", "Tactics", "Mindset", "Recovery")

CATEGORY_FOCUS = {
    "Train": {"Stamina": 8, "Speed": 7, "Strength": 7, "Agility": 7, "Mobility": 5, "Tactics": 3, "Mindset": 4, "Recovery": 4},
    "Recover": {"Stamina": 3, "Speed": 1, "Strength": 4, "Agility": 2, "Mobility": 9, "Tactics": 1, "Mindset": 5, "Recovery": 10},
    "Fuel": {"Stamina": 7, "Speed": 4, "Strength": 6, "Agility": 3, "Mobility": 2, "Tactics": 1, "Mindset": 5, "Recovery": 9},
    "Mind": {"Stamina": 2, "Speed": 2, "Strength": 1, "Agility": 2, "Mobility": 3, "Tactics": 6, "Mindset": 10, "Recovery": 6},
    "Tactics": {"Stamina": 4, "Speed": 5, "Strength": 2, "Agility": 6, "Mobility": 2, "Tactics": 10, "Mindset": 7, "Recovery": 2},
    "Ask": {"Stamina": 5, "Speed": 5, "Strength": 5, "Agility": 5, "Mobility": 5, "Tactics": 6, "Mindset": 6, "Recovery": 5},
}

MEALS = {
    "veg": ["Idli with sambar and peanut chutney", "Vegetable poha with peanuts", "Rajma chawal with salad",
            "Paneer bhurji wrap", "Dal, rice, curd and seasonal veg", "Sprouts chaat", "Banana + peanut butter toast",
            "Vegetable upma with curd", "Chana masala with rotis", "Curd rice with pomegranate"],
    "nonveg": ["Egg bhurji with whole-wheat toast", "Chicken curry with rice and salad", "Fish curry with red rice",
               "Boiled eggs and fruit", "Chicken wrap with veggies", "Egg fried rice with vegetables"],
    "vegan": ["Tofu stir-fry with rice", "Peanut-chickpea salad", "Oats with soy milk and banana",
              "Lentil soup with millet roti", "Soy chunk pulao"],
}


def _rng(feature: Feature, profile: dict, temperature: float) -> random.Random:
    key = f"{feature.id}|{profile.get('sport')}|{profile.get('position')}|{round(temperature, 1)}"
    return random.Random(zlib.crc32(key.encode()) if temperature < 0.35 else None)


def _pick(rng: random.Random, items: list[str], n: int, temperature: float) -> list[str]:
    pool = list(items)
    if temperature >= 0.35:
        rng.shuffle(pool)
    return pool[:n]


def _avoid_lines(profile: dict) -> list[str]:
    return [f"{inj}: {safety.INJURY_RULES[inj]}." for inj in profile.get("injuries", []) if inj in safety.INJURY_RULES]


def _meals(profile: dict) -> list[str]:
    diet = profile.get("diet", "")
    if diet == "Vegan":
        meals = MEALS["vegan"]
    elif diet in ("Non-vegetarian", "Halal"):
        meals = MEALS["veg"] + MEALS["nonveg"]
    else:
        meals = MEALS["veg"]
    allergens = [a.strip().lower().rstrip("s") for a in profile.get("allergies", "").split(",") if a.strip()]
    safe = [m for m in meals if not any(a and a in m.lower() for a in allergens)]
    return safe if len(safe) >= 3 else ["Rice, dal and seasonal vegetables", "Fruit and oats", "Millet roti with sabzi"]


PROTEIN_TEXT = {
    "Vegan": "tofu, soy chunks, lentils, chickpeas", "Vegetarian": "dal, paneer, curd, chana",
    "Jain": "dal, paneer, curd, moong", "Eggetarian": "dal, eggs, paneer, curd",
    "Pescatarian": "fish, dal, eggs, curd", "Halal": "halal chicken, eggs, dal", "Non-vegetarian": "chicken, fish, eggs, dal",
}


def _schedule(feature: Feature, profile: dict, extras: dict, rng: random.Random) -> list[PlanDay]:
    days_on = int(extras.get("days_per_week", 4)) if feature.id == "position_workout" else 5
    minutes = int(extras.get("session_minutes", 45))
    base = {"Low": 4, "Moderate": 6, "High": 7, "Very high": 8}.get(profile.get("intensity"), 6)
    if feature.category == "Recover" or profile.get("injuries"):
        base = max(2, base - 3)
    themes = {
        "Train": ["Strength & power", "Speed + agility", "Skill conditioning", "Position game drills", "Endurance intervals", "Mobility & core"],
        "Recover": ["Gentle mobility", "Pool / bike cardio", "Isometric strength", "Balance & control", "Band strength", "Walk + stretch"],
        "Fuel": ["Carb-loading day", "High-protein recovery", "Rainbow veg day", "Match-day fuel", "Iron-rich foods", "Hydration focus"],
        "Tactics": ["Scanning drills", "1v1 decisions", "Small-sided game", "Video study + shadow play", "Pressure decisions", "Team communication"],
        "Mind": ["Breathing", "Visualisation", "Cue words", "Routine rehearsal", "Reflection journal", "Rest"],
    }.get(feature.category, ["Training"] * 6)
    rest_days = {"Wed", "Sun"} if days_on <= 4 else {"Sun"}
    if days_on <= 3:
        rest_days = {"Tue", "Thu", "Sun"}
    plan, t = [], 0
    for day in DAYS:
        if day in rest_days and feature.category != "Fuel":
            plan.append(PlanDay(day=day, focus="Rest & recover", duration_min=0, intensity=0,
                                details="Light walk, stretching and 9+ hours of sleep."))
            continue
        theme = themes[t % len(themes)]
        t += 1
        intensity = max(1, min(10, base + rng.choice([-1, 0, 0, 1])))
        details = (", ".join(rng.sample(_meals(profile), 3)) if feature.category == "Fuel"
                   else f"{theme} block tailored to a {profile.get('position')}; keep RPE around {intensity}/10.")
        plan.append(PlanDay(day=day, focus=theme, duration_min=minutes if feature.category == "Train" else rng.choice([20, 30, 40]),
                            intensity=intensity, details=details))
    return plan


def generate(feature: Feature, profile: dict, extras: dict, temperature: float = 0.5) -> CoachPlan:
    rng = _rng(feature, profile, temperature)
    sport, pos = profile.get("sport", "Football (Soccer)"), profile.get("position", "player")
    name = profile.get("name") or "Champ"
    drills = SPORT_DRILLS.get(sport, GENERIC_DRILLS)
    avoid = _avoid_lines(profile) or ["No injuries reported — still stop if anything feels sharp or unusual."]
    goal = profile.get("goal", "Build stamina")

    sections_by_feature = {
        "position_workout": [
            Section(title=f"What a {pos} needs", icon="🎯", items=[
                f"Repeated high-intensity efforts typical of a {pos} in {sport}.",
                "Explosive first steps and quick deceleration.", "Core stability to stay strong in contact and balance.",
                f"Sport-specific endurance aligned with your goal: {goal.lower()}."]),
            Section(title="Strength & power", icon="💪", items=_pick(rng, [
                "Goblet or bodyweight squats, 3 × 10", "Glute bridges, 3 × 12", "Push-ups (incline if needed), 3 × 8-12",
                "Single-leg Romanian deadlift, 3 × 8", "Side planks, 3 × 25 s", "Broad jumps, 3 × 5 (skip if knee issues)"], 5, temperature)),
            Section(title="Speed, agility & conditioning", icon="⚡", items=_pick(rng, drills, 4, temperature)),
            Section(title="4-week progression", icon="📈", items=[
                "Week 1: learn the movements at RPE 5-6.", "Week 2: add one set to main lifts.",
                "Week 3: increase speed work volume by 10-15 %.", "Week 4: deload — 30 % less volume, test progress."]),
        ],
        "injury_recovery": [
            Section(title="Recovery phases", icon="🧭", items=[
                "Protect: pain-free daily movement, no impact.", "Restore: range of motion and light isometrics.",
                "Rebuild: progressive strength with bands and bodyweight.", "Return: sport drills only after a physio says yes."]),
            Section(title="Movements to avoid", icon="⛔", items=avoid),
            Section(title="Safe alternatives", icon="✅", items=[
                "Pool walking or stationary bike, 15-20 min", "Isometric wall sits, 5 × 20 s (pain ≤ 3/10)",
                "Band-resisted side steps, 3 × 10 each way", "Single-leg balance, 3 × 30 s",
                "Upper-body and core work to stay fit"]),
            Section(title="Check-ins", icon="🩺", items=[
                f"Stage: {extras.get('injury_stage', 'unknown')}. Pain now: {extras.get('pain_level', '?')}/10.",
                "Book a physio review every 2 weeks if possible.", "Track pain the morning after each session."]),
        ],
        "tactical_coach": [
            Section(title="What to scan for", icon="👀", items=[
                f"Before receiving, check over both shoulders — a {pos} needs a picture of space.",
                "Find the free player and the nearest opponent.", "Read the opponent's body shape for their next move."]),
            Section(title="If this → do that", icon="🔀", items=[
                "If you lose the ball → counter-press for 5 seconds, then recover shape.",
                "If the opponent is square-on → show them to their weaker side.",
                "If a teammate is under pressure → offer an angle and call 'man on'."]),
            Section(title="Drills that train it", icon="🧩", items=_pick(rng, drills, 2, temperature) + [
                f"Shadow play: walk through your {pos} movements against imaginary opponents, 5 min."]),
            Section(title="Common mistakes", icon="⚠️", items=[
                "Ball-watching instead of scanning.", "Silent play — talk early and loudly.",
                f"Over-committing — focus on: {extras.get('skill', 'positioning')}."]),
        ],
        "nutrition_week": [
            Section(title="Daily plate", icon="🍽️", items=[
                f"½ plate vegetables and fruit, ¼ carbs (rice, roti, millets), ¼ protein ({PROTEIN_TEXT.get(profile.get('diet'), 'dal, curd')}).",
                "Protein portion = your palm; carbs = your fist; fats = your thumb.",
                f"Diet: {profile.get('diet')}. Allergies excluded: {profile.get('allergies') or 'none'}."]),
            Section(title="Around training", icon="⏱️", items=[
                "2-3 h before: a normal meal rich in carbs.", "30-60 min before: banana or dates.",
                f"Within 1 h after: protein + carbs, e.g. {_meals(profile)[0].lower()}."]),
            Section(title="Budget tips", icon="💰", items=[
                f"Budget: {extras.get('budget', 'Moderate')} — seasonal produce and dals are cheapest per gram of protein.",
                "Chana, soy chunks and seasonal dals are high-protein and low-cost.", "Cook rice and dal in batches."]),
        ],
        "warmup_cooldown": [
            Section(title="Raise (3 min)", icon="🔥", items=["Light jog with arm swings", "Side shuffles and backpedal", "Skipping"]),
            Section(title="Activate & Mobilise (5 min)", icon="🌀", items=[
                "Glute bridges × 10", "World's greatest stretch × 4 each side", "Leg swings front/side × 10", "Ankle rocks × 10"]),
            Section(title="Potentiate (4 min)", icon="⚡", items=_pick(rng, drills, 2, temperature) + ["3 × 15 m build-up sprints"]),
            Section(title="Cool-down (10 min)", icon="🧊", items=[
                "Easy walk 3 min", "Hamstring, quad, calf, hip-flexor stretches — hold 30 s", "Box breathing 4-4-4-4 × 5"]),
        ],
        "mental_focus": [
            Section(title="Countdown routine", icon="⏳", items=[
                f"{extras.get('days_to_event', 7)} days out: write 3 process goals for {extras.get('event', 'the event')}.",
                "Every night: 5 min visualisation + 8-9 h sleep.", "Day before: pack kit, light session, early night."]),
            Section(title="Calm the nerves", icon="🫁", items=[
                "Box breathing: in 4, hold 4, out 4, hold 4 — five rounds.",
                "Nerves = your body getting ready. Rename 'nervous' to 'charged'.",
                f"Your nerves are {extras.get('nerves', 5)}/10 — that's normal before big games."]),
            Section(title="Mistake reset (10 s)", icon="🔄", items=[
                "Physical cue: tap your thigh / adjust your socks.", "Breathe out long.", "Say your cue word: 'NEXT'."]),
        ],
        "hydration": [
            Section(title="Timeline", icon="🕒", items=[
                "Day before: pale-yellow urine target, regular sips.", "2-3 h before: 400-600 ml water.",
                "During: 150-250 ml every 15-20 min.", "After: drink 1.5× the fluid you lost; add salty food."]),
            Section(title="Homemade electrolytes", icon="🍋", items=[
                "1 litre clean water + 6 level tsp sugar + ½ level tsp salt (WHO ORS-style).",
                "Coconut water + a pinch of salt.", "Lemon water with a pinch of salt and jaggery."]),
            Section(title="Danger signs", icon="🚨", items=[
                "Headache, dizziness, confusion or stopping sweating in heat → stop, shade, cool down, tell an adult.",
                f"Climate: {extras.get('climate', 'Hot & humid')} — train in cooler hours when possible."]),
        ],
        "visualization": [
            Section(title="Settle", icon="🌬️", items=["Close your eyes. Breathe in for 4… out for 6. Feel your feet on the ground."]),
            Section(title="Arrive", icon="🏟️", items=["You hear the crowd, smell the cut grass, feel your boots lace tight."]),
            Section(title="The moment", icon="🎯", items=[
                f"{extras.get('moment', 'Your big moment')}: you see your target, your body is loose, you execute exactly as trained."]),
            Section(title="Bounce-back", icon="🔄", items=["Something goes wrong. You breathe, tap your chest, say 'NEXT' and refocus."]),
            Section(title="Lock-in", icon="🔒", items=["Choose your cue word. Open your eyes ready."]),
        ],
        "decision_drills": [
            Section(title=f"Drill {i + 1}", icon="🎯", items=[d, "Decision cue: scan, choose, act within 2 seconds.",
                                                             "Score: +1 for the right choice, +1 for speed."])
            for i, d in enumerate(_pick(rng, drills, 4, temperature))
        ],
        "mobility_rehab": [
            Section(title=f"{extras.get('target_area', 'Hips')} flow", icon="🌀", items=[
                "Cat-cow × 8 breaths", "90/90 hip switches × 10", "Deep-squat hold (supported) 3 × 20 s",
                "Ankle circles × 10 each way", "Thread-the-needle × 6 each side", "Child's pose 60 s"]),
            Section(title="Rules", icon="📏", items=["Never force range.", "Pain must stay ≤ 3/10.", *avoid[:2]]),
            Section(title="Weekly self-test", icon="📊", items=["Knee-to-wall distance (cm)", "Sit-and-reach", "Single-leg balance time"]),
        ],
        "match_day": [
            Section(title="Morning", icon="🌅", items=["Wake 3+ h before playing, sip water.", "Familiar carb-rich breakfast."]),
            Section(title=f"Pre-match (start {extras.get('kickoff', '4 PM')})", icon="🎒", items=[
                "3 h before: main meal.", "Kit checklist: boots, shin pads, bottle, snack, spare socks.",
                "45 min before: RAMP warm-up.", "10 min before: breathing + cue word."]),
            Section(title="Half-time", icon="⏸️", items=["Sip fluids, orange slices or banana.", "One thing to keep, one thing to change."]),
            Section(title="After", icon="🌙", items=["Cool-down 10 min.", "Refuel within 1 h.", "Screens off 30 min before bed."]),
        ],
        "zero_equipment": [
            Section(title="Your gym = your space", icon="🏠", items=[
                f"Space: {extras.get('space', 'courtyard')}. Use a wall, stairs, a backpack with books, water bottles."]),
            Section(title="Circuit A — strength", icon="💪", items=[
                "Backpack squats 3 × 12", "Push-ups 3 × max-2", "Wall sit 3 × 30 s", "Single-leg glute bridge 3 × 10"]),
            Section(title="Circuit B — speed & engine", icon="⚡", items=_pick(rng, GENERIC_DRILLS, 3, temperature)),
            Section(title="Track progress without devices", icon="📒", items=[
                "Write reps in a notebook.", "Retest max push-ups every 2 weeks.", "Time a 1 km run with a friend's phone."]),
        ],
        "ask_coach": [
            Section(title="Quick answer", icon="💬", items=[
                f"For a {pos} in {sport}, this comes down to repetition under game-like pressure.",
                "Break the skill into small parts, master each, then add speed and opponents."]),
            Section(title="Try this drill", icon="🧩", items=_pick(rng, drills, 2, temperature)),
            Section(title="Why it works", icon="🔬", items=["Varied practice builds adaptable skills.",
                                                           "Short, focused sessions beat long tired ones."]),
        ],
    }

    sections = sections_by_feature.get(feature.id, sections_by_feature["ask_coach"])
    focus = CATEGORY_FOCUS.get(feature.category, CATEGORY_FOCUS["Ask"])
    jitter = 0 if temperature < 0.35 else 1
    focus_areas = [FocusArea(name=q, score=max(0, min(10, s + rng.randint(-jitter, jitter)))) for q, s in focus.items()]
    age = int(profile.get("age", 15))
    macros = None
    if feature.wants_macros:
        kcal = 2000 + (age - 12) * 80 + (300 if profile.get("intensity") in ("High", "Very high") else 0)
        macros = Macros(calories=int(min(3400, max(1800, kcal))), protein_pct=20, carbs_pct=55, fat_pct=25)

    openers = ["Let's go", "Locked in", "Game on", "Your move", "Built for you"]
    return CoachPlan(
        headline=f"{rng.choice(openers)}, {name}: {feature.title} for a {pos}",
        summary=(f"A {feature.title.lower()} designed for a {age}-year-old {pos} in {sport}, aimed at "
                 f"'{goal.lower()}'. Everything respects your injury history, {profile.get('equipment', 'equipment').lower()} "
                 f"and a {profile.get('intensity', 'moderate').lower()} intensity preference."),
        sections=sections,
        weekly_plan=_schedule(feature, profile, extras, rng) if feature.wants_schedule else [],
        focus_areas=focus_areas,
        macros=macros,
        safety_notes=[*avoid[:3],
                      *(["Multiple injuries: keep every session low-impact and get a physio to review this plan."]
                        if len(profile.get("injuries", [])) >= 3 else []),
                      "Stop if you feel sharp pain, swelling, dizziness or chest discomfort, and tell a coach or parent."],
        coach_message=rng.choice([
            "Small wins every day become big wins on match day. 🔥",
            "Consistency beats intensity — show up, do the work, recover well.",
            "You don't need a fancy gym to become elite. You need a plan and you've got one.",
        ]),
    )
