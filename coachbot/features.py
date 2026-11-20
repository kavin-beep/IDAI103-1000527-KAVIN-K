"""The 13 CoachBot prompt features.

Each feature is a versioned prompt template with its own recommended sampling
parameters. Changelog notes record design-review iterations made while writing the
prompts (the risk each change addresses); live-model findings belong in
research/VALIDATION.md after running eval/run_eval.py with a Gemini key. Safety-critical features run cold (0.2-0.3) so plans stay
conservative; creative features (mindset, visualisation, tactics) run warmer
(0.7-0.9) for variety. The changelog records how each prompt was refined.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Extra:
    """A feature-specific input shown under the feature in the UI."""

    key: str
    label: str
    kind: str = "text"  # text | select | slider | area
    options: tuple = ()
    default: object = ""
    help: str = ""


@dataclass(frozen=True)
class Feature:
    id: str
    title: str
    emoji: str
    category: str  # Train | Recover | Fuel | Mind | Tactics | Ask
    tagline: str
    template: str
    temperature: float
    top_p: float
    top_k: int
    accent: str
    wants_schedule: bool = False
    wants_macros: bool = False
    extras: tuple[Extra, ...] = ()
    version: str = "v1"
    changelog: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def render(self, profile_block: str, values: dict[str, str]) -> str:
        return self.template.format(profile=profile_block, **values)


FEATURES: tuple[Feature, ...] = (
    Feature(
        id="position_workout",
        title="Position Workout",
        emoji="🏋️",
        category="Train",
        tagline="A full-body plan built for the demands of your exact position.",
        accent="#C6FF3D",
        temperature=0.4, top_p=0.9, top_k=40,
        wants_schedule=True,
        extras=(Extra("days_per_week", "Training days per week", "slider", (2, 6), 4),
                Extra("session_minutes", "Minutes per session", "slider", (20, 90), 45)),
        template="""TASK: Generate a full-body workout plan for a {position} in {sport}.
{profile}
Sessions: {days_per_week} days per week, about {session_minutes} minutes each.

Explain which physical qualities a {position} needs most (e.g. repeated sprints,
explosive jumps, rotational power) and build every session around them. Include
position-specific movement patterns, sets x reps or time, and progressions.
Fill weekly_plan with 7 days (rest days included, intensity 0). Sections: Position
demands, Strength & power, Speed/agility/conditioning, Skill-linked drills,
Progression for the next 4 weeks.""",
        version="v3",
        changelog=(("v1", "Draft: generic 'workout for a {position}' prompt. Review risk: gym-heavy plans that ignore position demands."),
                   ("v2", "Added an explicit 'physical qualities a {position} needs' step so every session is anchored to position demands."),
                   ("v3", "Required a 7-day weekly_plan with rest days and a 4-week progression, so recovery is always scheduled.")),
    ),
    Feature(
        id="injury_recovery",
        title="Injury-Safe Recovery",
        emoji="🩹",
        category="Recover",
        tagline="Train around a past injury with low-risk, coach-approved alternatives.",
        accent="#3DF5FF",
        temperature=0.2, top_p=0.8, top_k=20,
        wants_schedule=True,
        extras=(Extra("injury_stage", "Where are you in recovery?", "select",
                      ("Cleared by doctor/physio, rebuilding", "Mostly pain-free, not yet cleared",
                       "Old injury, want to prevent re-injury"), "Old injury, want to prevent re-injury"),
                Extra("pain_level", "Pain during daily activity (0-10)", "slider", (0, 10), 1)),
        template="""TASK: Create a safe recovery training schedule for an athlete with: {injuries}.
{profile}
Recovery stage: {injury_stage}. Current pain in daily life: {pain_level}/10.

Use a conservative, phase-based approach (protect → restore → rebuild → return).
For every exercise prefer low-impact options (pool, bike, isometrics, bands).
List movements to AVOID for this injury and explain why. Include clear stop signs
(sharp pain, swelling, instability) and recommend physio check-ins. Never state that
the athlete is cleared to play. Fill weekly_plan with a gentle 7-day schedule.""",
        version="v3",
        changelog=(("v1", "Draft at the default temperature. Review risk: creative sampling could suggest high-impact work for an injured athlete."),
                   ("v2", "Lowered to temperature 0.2 / top_p 0.8 and added an explicit AVOID list per injury."),
                   ("v3", "Added a pain-level input and a 'never state cleared to play' rule for edge cases.")),
    ),
    Feature(
        id="tactical_coach",
        title="Tactical IQ Coach",
        emoji="🧠",
        category="Tactics",
        tagline="Game-reading tips and scenarios to sharpen a specific skill.",
        accent="#FF3DAE",
        temperature=0.7, top_p=0.95, top_k=40,
        extras=(Extra("skill", "Skill to improve", "text", default="Positioning when we lose the ball"),
                Extra("level_of_play", "Level of opposition", "select",
                      ("School friendlies", "Inter-school league", "District / state", "Academy"), "Inter-school league")),
        template="""TASK: Provide tactical coaching tips to improve "{skill}" in {sport} for a {position}.
{profile}
Opposition level: {level_of_play}.

Teach like a youth coach on the touchline: what to scan for, where to be, when to
act, and how to communicate with teammates. Give 3 realistic match scenarios with
"if this → do that" decisions, 2 small-sided games or drills that train the skill,
common mistakes for this position, and one video-study habit.""",
        version="v2",
        changelog=(("v1", "Draft: open-ended tips request. Review risk: generic advice ('stay focused') with no position context."),
                   ("v2", "Added 'if this → do that' scenarios, communication cues and position-specific mistakes.")),
    ),
    Feature(
        id="nutrition_week",
        title="7-Day Fuel Plan",
        emoji="🥗",
        category="Fuel",
        tagline="A week of affordable, culturally-friendly meals for a growing athlete.",
        accent="#FFB13D",
        temperature=0.6, top_p=0.9, top_k=40,
        wants_schedule=True, wants_macros=True,
        extras=(Extra("budget", "Food budget", "select", ("Tight", "Moderate", "Flexible"), "Moderate"),
                Extra("cuisine", "Preferred cuisine / region", "text", default="South Indian home food")),
        template="""TASK: Suggest a week-long nutrition guide for a {age}-year-old {sport} athlete following a {diet} diet.
{profile}
Budget: {budget}. Cuisine preference: {cuisine}.

Focus on whole, affordable, locally available foods. Cover breakfast, lunch, dinner,
pre-training and post-training snacks. Respect allergies strictly. Explain portion
sizes in hands/cups, not grams. Fill weekly_plan with 7 days where 'focus' is the
day's theme and 'details' lists the meals; use intensity for that day's training load.
Fill macros with a sensible daily calorie target and macro split for a youth athlete.
No supplements, fasting, or weight-cutting advice.""",
        version="v3",
        changelog=(("v1", "Draft: open nutrition request. Review risk: supplement or adult-sized calorie advice for minors."),
                   ("v2", "Banned supplements/weight-cutting; asked for portions in hands/cups for accessibility."),
                   ("v3", "Added budget + regional cuisine inputs so plans fit low-resource households.")),
    ),
    Feature(
        id="warmup_cooldown",
        title="Warm-Up & Cool-Down",
        emoji="🔥",
        category="Train",
        tagline="A sport-specific RAMP warm-up and a recovery cool-down.",
        accent="#FF6A3D",
        temperature=0.3, top_p=0.85, top_k=30,
        extras=(Extra("available_minutes", "Minutes available before play", "slider", (8, 30), 15),),
        template="""TASK: Generate a personalised warm-up and cool-down routine for a {position} in {sport}.
{profile}
Time available for the warm-up: {available_minutes} minutes.

Structure the warm-up with the RAMP method (Raise, Activate, Mobilise, Potentiate)
with timings for each block, then a 10-minute cool-down (easy movement, static
stretches with hold times, breathing). Add injury-prevention exercises for the
athlete's injury history and position (e.g. FIFA 11+ style for footballers).""",
        version="v2",
        changelog=(("v1", "Draft: generic routine. Review risk: long static stretching before play."),
                   ("v2", "Switched to RAMP structure with dynamic warm-up and static stretches only in the cool-down.")),
    ),
    Feature(
        id="mental_focus",
        title="Tournament Mindset",
        emoji="🧘",
        category="Mind",
        tagline="Beat pre-match nerves with focus routines that actually work.",
        accent="#9D7BFF",
        temperature=0.8, top_p=0.95, top_k=50,
        extras=(Extra("event", "Upcoming event", "text", default="School zonal tournament"),
                Extra("days_to_event", "Days until the event", "slider", (1, 30), 7),
                Extra("nerves", "How nervous do you feel? (0-10)", "slider", (0, 10), 6)),
        template="""TASK: Build a mental focus routine for tournaments.
{profile}
Event: {event}, in {days_to_event} days. Nerves level: {nerves}/10.

Include a daily countdown routine, box-breathing or similar technique, a personal
cue word, a pre-performance routine for the {position}, how to reset after a mistake
in under 10 seconds, and healthy sleep habits before the event. Normalise nerves and
keep it age-appropriate. If nerves are 9-10, gently suggest talking to a trusted adult.""",
        version="v2",
        changelog=(("v1", "Draft: 'mental tips' request. Review risk: abstract quotes instead of usable techniques."),
                   ("v2", "Required concrete techniques (breathing, cue word, mistake reset) and a countdown.")),
    ),
    Feature(
        id="hydration",
        title="Hydration & Electrolytes",
        emoji="💧",
        category="Fuel",
        tagline="Drink the right amount at the right time — for your climate.",
        accent="#3D9BFF",
        temperature=0.4, top_p=0.85, top_k=30,
        extras=(Extra("climate", "Training climate", "select",
                      ("Hot & humid", "Hot & dry", "Mild", "Cold"), "Hot & humid"),
                Extra("session_length", "Typical session length (min)", "slider", (30, 180), 90),
                Extra("match_time", "Match / training time", "select",
                      ("Early morning", "Midday", "Afternoon", "Evening"), "Afternoon")),
        template="""TASK: Create a hydration and electrolyte strategy.
{profile}
Climate: {climate}. Session length: {session_length} minutes. Usual time: {match_time}.

Give a timeline (the day before, 2-3 h before, during, after), simple urine-colour
checks, low-cost homemade electrolyte options (e.g. ORS-style, coconut water, lemon
salt water) with safe proportions, warning signs of dehydration and heat illness,
and when energy/sports drinks are or are not useful for a teenager.""",
        version="v2",
        changelog=(("v1", "Draft: generic hydration request. Review risk: only commercial sports drinks suggested."),
                   ("v2", "Added low-cost homemade options and heat-illness warning signs for hot climates.")),
    ),
    Feature(
        id="visualization",
        title="Pre-Match Visualisation",
        emoji="🎬",
        category="Mind",
        tagline="A cinematic guided-imagery script starring you.",
        accent="#FF3D6E",
        temperature=0.9, top_p=0.95, top_k=60,
        extras=(Extra("moment", "Moment to rehearse", "text", default="Taking a penalty in the final minute"),),
        template="""TASK: Write a pre-match visualisation script for a {position} in {sport}.
{profile}
Key moment to rehearse: {moment}.

Use all five senses, first-person present tense, and the PETTLEP model (Physical,
Environment, Task, Timing, Learning, Emotion, Perspective). Sections: Settle (breathing),
Arrive (venue sensations), The moment (step by step, success imagery), Bounce-back
(handling a setback calmly), Lock-in (cue word). About 3 minutes when read aloud.""",
        version="v2",
        changelog=(("v1", "Draft: generic visualisation request. Review risk: third-person, generic script."),
                   ("v2", "Applied PETTLEP model, first-person present tense and a bounce-back segment.")),
    ),
    Feature(
        id="decision_drills",
        title="Decision-Making Drills",
        emoji="🎯",
        category="Tactics",
        tagline="Positional drills that train faster, smarter decisions under pressure.",
        accent="#3DFF9E",
        temperature=0.7, top_p=0.9, top_k=40,
        wants_schedule=True,
        extras=(Extra("players_available", "Players usually available", "select",
                      ("Just me", "2-4 friends", "Small squad (5-10)", "Full team"), "2-4 friends"),),
        template="""TASK: Design positional decision-making drills for a {position} in {sport}.
{profile}
Players available: {players_available}.

Give 4-5 drills that each train perception → decision → action with a time
pressure or opponent. For each: setup (space, equipment that matches the athlete's
access), rules, decision cues, progressions and how to score it. Fill weekly_plan
with a 7-day schedule that rotates the drills.""",
        version="v2",
        changelog=(("v1", "Draft: drills request. Review risk: assumes a full team and equipment, unusable for solo athletes."),
                   ("v2", "Added players-available input and required equipment to match the athlete's access.")),
    ),
    Feature(
        id="mobility_rehab",
        title="Mobility Flow",
        emoji="🌀",
        category="Recover",
        tagline="Gentle mobility flows for post-injury range of motion.",
        accent="#3DE6FF",
        temperature=0.3, top_p=0.85, top_k=30,
        extras=(Extra("target_area", "Area that feels tight", "select",
                      ("Hips", "Ankles", "Hamstrings", "Shoulders", "Thoracic spine", "Full body"), "Hips"),
                Extra("flow_minutes", "Minutes per flow", "slider", (5, 30), 12)),
        template="""TASK: Create a mobility workout for post-injury recovery focused on the {target_area}.
{profile}
Duration: {flow_minutes} minutes, suitable for daily use.

Sequence 6-8 gentle movements with reps or hold times, breathing cues and
regressions. Respect the injury history: no forcing range, no pain above 3/10.
Include a quick self-test to track improvement weekly.""",
        version="v1",
        changelog=(("v1", "Initial version with pain-ceiling rule (≤3/10) from the start."),),
    ),
    Feature(
        id="match_day",
        title="Match-Day Game Plan",
        emoji="🏟️",
        category="Mind",
        tagline="Hour-by-hour plan: fuel, warm-up, mindset and recovery.",
        accent="#C6FF3D",
        temperature=0.5, top_p=0.9, top_k=40,
        extras=(Extra("kickoff", "Kick-off / start time", "text", default="4:00 PM"),),
        template="""TASK: Build a complete match-day game plan for a {position} in {sport}.
{profile}
Start time: {kickoff}.

Make a timeline from waking up to bedtime: meals and snacks (matching diet and
allergies), hydration, travel/kit checklist, warm-up, half-time reset, mental cues,
and post-match recovery (cool-down, refuel within an hour, sleep). Keep it realistic
for a student with school commitments.""",
        version="v1",
        changelog=(("v1", "Combines warm-up, fuel and mindset prompts into one timeline."),),
    ),
    Feature(
        id="zero_equipment",
        title="Zero-Equipment Training",
        emoji="🏠",
        category="Train",
        tagline="Elite-level conditioning with nothing but bodyweight and a wall.",
        accent="#FFE03D",
        temperature=0.5, top_p=0.9, top_k=40,
        wants_schedule=True,
        extras=(Extra("space", "Space available", "select",
                      ("Small room", "Courtyard / terrace", "Open field or street", "Stairs available"),
                      "Courtyard / terrace"),),
        template="""TASK: Build a 7-day zero-equipment training plan for a {position} in {sport}.
{profile}
Space available: {space}.

Assume no gym, no weights, and possibly no coach — use bodyweight, walls, stairs,
household items (water bottles, backpack) and partner exercises. Keep it safe for
the athlete's age and injuries. Fill weekly_plan with 7 days and include a simple
way to track progress without devices.""",
        version="v2",
        changelog=(("v1", "Draft: 'home workout' request. Review risk: still assumes bands and cones."),
                   ("v2", "Strict no-equipment rule and household-item substitutions for under-resourced athletes.")),
    ),
    Feature(
        id="ask_coach",
        title="Ask CoachBot",
        emoji="💬",
        category="Ask",
        tagline="Any sports question — answered for your sport, position and age.",
        accent="#FFFFFF",
        temperature=0.6, top_p=0.9, top_k=40,
        extras=(Extra("question", "Your question", "area",
                      default="How can I improve my first touch when the ball comes in fast?"),),
        template="""TASK: Answer the athlete's question as their personal youth coach.
{profile}
Question: "{question}"

Answer specifically for their sport, position, age and level. Give practical steps,
one drill if useful, and the reasoning behind it. If the question is outside sport,
fitness, nutrition or wellbeing, politely steer back to sport.""",
        version="v1",
        changelog=(("v1", "Free-form question routed through the same safety screen and JSON contract."),),
    ),
)

FEATURES_BY_ID = {f.id: f for f in FEATURES}
CATEGORY_COLORS = {
    "Train": "#C6FF3D", "Recover": "#3DF5FF", "Fuel": "#FFB13D",
    "Mind": "#9D7BFF", "Tactics": "#FF3DAE", "Ask": "#FFFFFF",
}
