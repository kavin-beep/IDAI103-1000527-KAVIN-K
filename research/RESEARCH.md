# CoachBot AI — Research notes

## 1. The problem

NextGen Sports Lab's brief: many young athletes, especially in under-resourced regions or at early stages, have no access to professional coaches or tailored routines. What they find online is usually:

- **Position-blind.** A goalkeeper, a fast bowler and a point guard get the same "football workout" or "gym plan".
- **Injury-blind.** Generic plans don't change for an ankle sprain, knee strain or growth-plate pain (Osgood-Schlatter, Sever's), which are common in youth sport.
- **Resource-blind.** They assume a gym, cones, supplements or expensive foods.
- **Not built for minors.** Adult loading, calorie targets and "no pain, no gain" messaging are not appropriate for 8–18-year-olds.

## 2. Findings that shaped the design

| Finding | Source | How CoachBot uses it |
|---|---|---|
| Youth training should be technique-first and age-appropriate, with loading that progresses with maturity. | Lloyd & Oliver (2012), *The Youth Physical Development Model* | Hard constraints for under-13s (bodyweight and play only) and 13–15s (light loads, no 1RM testing), added by `safety.screen_input`. |
| Structured neuromuscular warm-ups reduce injuries in youth football. | Soligard et al. (2008), BMJ, the FIFA 11+ programme | The Warm-Up & Cool-Down feature uses the RAMP structure and FIFA 11+-style prevention work. |
| Position changes the physical demands: repeated sprints vs. explosive dives vs. rotational power. | ExRx.net workout library; sport-science coaching texts | The Position Workout prompt asks Gemini to reason about "what a {position} needs" before writing sessions. |
| Common youth injuries need specific modifications, not just "rest". | NCBI Bookshelf NBK566046 (youth sports injuries) | 12 injury rule sets in `INJURY_RULES` become "avoid / prefer" constraints in the prompt. |
| Motor imagery works best when it is multi-sensory and realistic. | Holmes & Collins (2001), the PETTLEP model | The Pre-Match Visualisation prompt follows PETTLEP in first-person present tense. |
| Low-cost oral rehydration can be made at home. | WHO oral rehydration guidance | Hydration feature suggests ORS-style, coconut water and lemon-salt options for hot climates. |
| LLM output quality depends on persona, a clear task, structured context, constraints and an output format. | Google, *Gemini API prompting strategies* | Every request has a system persona, a TASK line, a labelled profile block, HARD CONSTRAINTS and a JSON schema. |
| AI fitness apps succeed when outputs are personalised and actionable, and fail when generic. | IJISRT, *AI-powered fitness web app*; TIJER, *AI fitness assistant*; Medium, *Building a GenAI fitness app with Gemini* | Structured JSON output, schedules, charts, downloads and per-feature tuning. |
| Nutrition advice for young athletes should be food-first, not supplement-first. | eatright.org (Academy of Nutrition and Dietetics) | The 7-Day Fuel Plan bans supplements and weight-cutting, gives portions in hands/cups and respects regional cuisine and budget. |

## 3. Objectives → features

| Objective from the brief | CoachBot implementation |
|---|---|
| Empower youth with AI-based personal training | 13 Gemini features, a profile-driven prompt and 14 response languages |
| Adaptive routines by physical condition and position | 12 sports and 64 positions mapped, injury rules, age rules, equipment levels |
| Safety, motivation and nutrition awareness | Safety screen and output scan, 4 coach personas, XP and badges, nutrition and hydration features |
| Accessibility for low-resource areas | Zero-Equipment Training, budget and regional-cuisine inputs, a demo mode that runs without a key, mobile-responsive UI |

## 4. References

1. Google AI — *Gemini API prompting strategies*. https://ai.google.dev/gemini-api/docs/prompting-strategies
2. Google AI — *Gemini API key*. https://ai.google.dev/gemini-api/docs/api-key
3. Lloyd, R. S., & Oliver, J. L. (2012). The Youth Physical Development Model: A new approach to long-term athletic development. *Strength and Conditioning Journal*, 34(3), 61–72.
4. Soligard, T., et al. (2008). Comprehensive warm-up programme to prevent injuries in young female footballers: cluster randomised controlled trial. *BMJ*, 337, a2469.
5. Holmes, P. S., & Collins, D. J. (2001). The PETTLEP approach to motor imagery. *Journal of Applied Sport Psychology*, 13(1), 60–83.
6. NCBI Bookshelf NBK566046. https://www.ncbi.nlm.nih.gov/books/NBK566046/
7. ExRx.net — Workout menu. https://exrx.net/Lists/WorkoutMenu
8. Academy of Nutrition and Dietetics. https://www.eatright.org/
9. IJISRT — Artificial-intelligence-powered fitness web app. https://www.ijisrt.com/artificial-intelligence-powered-fitness-web-app
10. TIJER — AI fitness assistant. https://tijer.org/tijer/papers/TIJERC001307.pdf
11. Dimeloper — Building a GenAI fitness app with Gemini. https://medium.com/@dimeloper/building-a-genai-fitness-app-with-gemini-1229f7c369e7
12. IBM — Develop an AI personal trainer. https://www.ibm.com/think/tutorials/develop-ai-personal-trainer-with-llama-4-watsonx-ai
