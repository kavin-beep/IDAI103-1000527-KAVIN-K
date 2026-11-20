"""Youth-athlete safety layer: screens input before Gemini and output after it."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Symptoms that need a medical professional, not a training plan.
RED_FLAGS: dict[str, str] = {
    r"chest (pain|tight)": "chest pain or tightness",
    r"faint|passed out|black(ed)? out": "fainting or blacking out",
    r"can'?t breathe|short(ness)? of breath": "trouble breathing",
    r"heart (racing|flutter)|palpitation": "an irregular heartbeat",
    r"(hit|bang|knock)(ed)? (my |on the )?head|concuss(ion|ed) (yesterday|today|this week)": "a recent head injury",
    r"(dizzy|vomit|throw(ing)? up).{0,40}(head|hit|fall)": "possible concussion symptoms",
    r"numb|tingling|pins and needles": "numbness or tingling",
    r"(bone|joint).{0,20}(deform|sticking out|out of place)|dislocat": "a possible fracture or dislocation",
    r"(can'?t|cannot) (walk|put weight)": "being unable to bear weight",
    r"blood in (my )?(urine|pee)": "blood in urine",
    r"severe (pain|swelling)": "severe pain or swelling",
}

# Requests CoachBot refuses for minors.
BLOCKED: dict[str, str] = {
    r"steroid|sarms?\b|anabolic|hgh|growth hormone|testosterone": "performance-enhancing drugs",
    r"starv|stop eating|skip(ping)? (all )?meals|eat nothing|purg": "restrictive or unsafe eating",
    r"lose \d+\s?(kg|kilos?|pounds|lbs) (in|within) (a|one|\d+) (day|week)": "rapid weight loss",
    r"sauna suit|sweat(ing)? (off|out) weight|make weight fast": "dehydration weight-cutting",
    r"play through (the )?(pain|injury)|ignore (the )?pain": "training through pain",
}

# How each injury changes the plan. Sent to Gemini as hard constraints.
INJURY_RULES: dict[str, str] = {
    "Ankle sprain": "avoid sharp cutting, jumping/landing on uneven ground; include balance and ankle-strength work",
    "Knee strain": "avoid deep loaded squats, high-impact lunges, jumping and plyometrics; prefer pool, bike, isometrics",
    "Hamstring strain": "no maximal sprints or heavy eccentric loading early; build with bridges and progressive tempo runs",
    "Groin strain": "avoid wide lateral lunges and explosive change of direction early; include adductor isometrics",
    "Shoulder injury": "avoid overhead pressing, heavy pulling and high throwing/bowling volume; use band rotator-cuff work",
    "Lower back pain": "avoid heavy spinal loading and loaded flexion; prioritise core stability and hip mobility",
    "Shin splints": "reduce running volume on hard surfaces, no sudden mileage jumps; cross-train and strengthen calves",
    "Wrist injury": "avoid weight-bearing on hands (push-ups, planks on palms); use forearm planks",
    "Tennis/golfer's elbow": "limit gripping and racket/throwing volume; include eccentric wrist work",
    "Previous concussion": "no heading, contact or collision drills unless medically cleared; flag any returning symptoms",
    "Osgood-Schlatter (knee growth pain)": "limit jumping and kneeling; keep load pain-free and stretch quads gently",
    "Sever's (heel growth pain)": "limit running on hard surfaces and barefoot jumping; calf stretching and cushioned shoes",
}

UNSAFE_OUTPUT = re.compile(
    r"steroid|sarms|creatine loading|fat burner|pre-workout|no pain,? no gain|push through (the )?pain|"
    r"fast(ing)? for \d+ days|\b(800|900|1000) ?kcal\b",
    re.IGNORECASE,
)


@dataclass
class Screen:
    allowed: bool = True
    reason: str = ""
    kind: str = ""  # red_flag | blocked
    constraints: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def screen_input(profile: dict, free_text: str) -> Screen:
    """Check free text for emergencies or refused requests and build plan constraints."""
    text = f"{free_text} {profile.get('injury_notes', '')}".lower()
    for pattern, label in RED_FLAGS.items():
        if re.search(pattern, text):
            return Screen(False, f"You mentioned {label}. That needs a doctor or physio before any training plan.", "red_flag")
    for pattern, label in BLOCKED.items():
        if re.search(pattern, text):
            return Screen(False, f"CoachBot can't help with {label} — it isn't safe for young athletes.", "blocked")

    result = Screen()
    for injury in profile.get("injuries", []):
        if injury in INJURY_RULES:
            result.constraints.append(f"{injury}: {INJURY_RULES[injury]}")
    age = int(profile.get("age", 15))
    if age < 13:
        result.constraints.append("Under 13: bodyweight and play-based training only, no external heavy loads, fun first")
    elif age < 16:
        result.constraints.append("Age 13-15: technique-first strength training, light loads, no 1-rep-max testing")
    calories = int(profile.get("calories") or 0)
    if calories and not 1400 <= calories <= 4000:
        result.warnings.append("Your calorie goal looks unusual for a youth athlete, so CoachBot will suggest a safe range instead.")
        result.constraints.append("Ignore the supplied calorie goal; recommend a safe range for the athlete's age and sport")
    if profile.get("allergies"):
        result.constraints.append(f"Strictly exclude allergens: {profile['allergies']}")
    if len(profile.get("injuries", [])) >= 3:
        result.warnings.append("Multiple injuries listed — CoachBot will keep everything low-impact. Please check with a physio.")
        result.constraints.append("Multiple injuries: keep every exercise low-impact and recommend a physiotherapist review")
    return result


def screen_output(text: str) -> list[str]:
    """Return phrases in the model output that break CoachBot's safety rules."""
    return sorted({m.group(0).lower() for m in UNSAFE_OUTPUT.finditer(text)})
