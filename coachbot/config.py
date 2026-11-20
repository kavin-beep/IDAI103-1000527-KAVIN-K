"""Central settings for CoachBot AI. Never put API keys in this file."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "CoachBot AI"
APP_TAGLINE = "Your AI virtual coach — built for the next generation of athletes."

# ── Gemini models ────────────────────────────────────────────────────────────
# The brief names Gemini 1.5 Pro. Google retired the 1.5 family in 2025, so the
# app targets its successors. The "-latest" aliases always point at the newest
# stable model, which keeps the deployed app working after future retirements.
# Any model id can also be typed in the sidebar, and "List my models" asks the
# API which ids your key can use.
MODEL_OPTIONS = (
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
)
DEFAULT_MODEL = MODEL_OPTIONS[0]

# ── Generation defaults (overridden per feature, see features.py) ───────────
DEFAULT_TEMPERATURE = 0.5
DEFAULT_TOP_P = 0.9
DEFAULT_TOP_K = 40
DEFAULT_MAX_TOKENS = 4096
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 1.5

# Temperature grid used by the Tuning Lab and eval/run_eval.py
TEMPERATURE_GRID = (0.2, 0.5, 0.9)
TOP_P_GRID = (0.8, 0.95)

# ── Paths ────────────────────────────────────────────────────────────────────
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "coachbot_log.jsonl"
EVAL_DIR = ROOT / "eval"
EVAL_RESULTS_DIR = EVAL_DIR / "results"

# ── Athlete profile options ──────────────────────────────────────────────────
SPORT_POSITIONS: dict[str, list[str]] = {
    "Football (Soccer)": ["Goalkeeper", "Centre-back", "Full-back", "Defensive midfielder",
                          "Central midfielder", "Attacking midfielder", "Winger", "Striker"],
    "Cricket": ["Fast bowler", "Spin bowler", "Opening batter", "Middle-order batter",
                "Wicket-keeper", "All-rounder"],
    "Basketball": ["Point guard", "Shooting guard", "Small forward", "Power forward", "Center"],
    "Athletics": ["Sprinter (100–400 m)", "Middle distance", "Long distance", "Jumper",
                  "Thrower", "Hurdler"],
    "Tennis": ["Baseliner", "Serve-and-volley", "All-court player", "Doubles specialist"],
    "Hockey": ["Goalkeeper", "Defender", "Midfielder", "Forward"],
    "Volleyball": ["Setter", "Outside hitter", "Middle blocker", "Opposite", "Libero"],
    "Badminton": ["Singles", "Doubles – front court", "Doubles – back court"],
    "Kabaddi": ["Raider", "Defender – corner", "Defender – cover", "All-rounder"],
    "Swimming": ["Sprint freestyle", "Distance freestyle", "Backstroke", "Breaststroke",
                 "Butterfly", "Individual medley"],
    "Rugby": ["Prop", "Hooker", "Lock", "Flanker", "Scrum-half", "Fly-half", "Centre", "Wing",
              "Full-back"],
    "Baseball": ["Pitcher", "Catcher", "Infielder", "Outfielder"],
}

INJURY_OPTIONS = (
    "Ankle sprain", "Knee strain", "Hamstring strain", "Groin strain", "Shoulder injury",
    "Lower back pain", "Shin splints", "Wrist injury", "Tennis/golfer's elbow",
    "Previous concussion", "Osgood-Schlatter (knee growth pain)", "Sever's (heel growth pain)",
)

EXPERIENCE_LEVELS = ("Beginner", "Developing", "Club / school team", "Academy / district", "Elite youth")
INTENSITY_LEVELS = ("Low", "Moderate", "High", "Very high")
TRAINING_STYLES = ("Bodyweight", "Field drills", "Gym / weights", "Plyometrics",
                   "Yoga & mobility", "Swimming / pool", "Cycling", "Partner drills")
EQUIPMENT_LEVELS = ("No equipment", "Basic (ball, cones, bands)", "School / club facility", "Full gym")
DIET_TYPES = ("Non-vegetarian", "Vegetarian", "Eggetarian", "Vegan", "Jain", "Halal", "Pescatarian")
GOALS = ("Build stamina", "Post-injury recovery", "Tactical improvement", "Speed & agility",
         "Strength & power", "Flexibility & mobility", "Tournament preparation", "Skill technique")
LANGUAGES = ("English", "Hindi", "Tamil", "Telugu", "Bengali", "Marathi", "Kannada", "Malayalam",
             "Urdu", "Spanish", "French", "Portuguese", "Arabic", "Swahili")
COACH_TONES = {
    "Hype Coach": "high-energy, motivating, uses short punchy sentences and sports slang a teenager enjoys",
    "Calm Mentor": "calm, patient and reassuring; explains the why behind every step",
    "Pro Analyst": "precise and technical like an academy performance analyst, still age-appropriate",
    "Big Sibling": "friendly, relatable and encouraging, like an older teammate who has been there",
}

SAFETY_DISCLAIMER = (
    "CoachBot gives general training education, not medical advice. For pain, injury or "
    "return-to-play decisions, talk to a doctor, physiotherapist or qualified coach."
)
