# app/quiz_app.py
# SportSync — Quiz + Layer Z (light) with optional OpenAI refine

import os
import json
from typing import Dict, List, Tuple
import streamlit as st

# ---------------------------  UI Setup  ---------------------------
st.set_page_config(page_title="SportSync — Quiz", layout="centered")
st.title("SportSync — Find your sport")

st.caption(
    "Answer a few questions. We'll infer your intent (Layer Z lite) "
    "and recommend up to 3 sports. If you add an OpenAI key later, "
    "refinement becomes smarter automatically."
)

# --------------------  Optional OpenAI (if present)  --------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
USE_AI = False
openai_client = None

if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        USE_AI = True
    except Exception:
        USE_AI = False  # fallback silently


# ----------------------  Questions Definition  ----------------------
with st.form("sport_quiz"):
    lang = st.selectbox("Language", ["en", "ar"], index=0)

    goal = st.multiselect(
        "Your main goals",
        [
            "Lose weight", "Build muscle", "Improve endurance",
            "Flexibility & mobility", "Fun / gamified (VR)", "Skills / technique"
        ],
    )

    intensity = st.select_slider(
        "Preferred intensity", options=["Low", "Moderate", "High"], value="Moderate"
    )

    social = st.selectbox(
        "How do you like to train?",
        ["Solo", "Duo/Partner", "Team"]
    )

    place = st.multiselect(
        "Where can you train?",
        ["Home", "Gym", "Outdoor", "Pool", "Studio"]
    )

    equipment = st.multiselect(
        "Available equipment",
        ["None", "Free weights", "Bike (indoor/outdoor)", "Rower", "Pool access", "Yoga mat"]
    )

    constraints = st.multiselect(
        "Constraints / injuries (optional)",
        ["Knee pain", "Back pain", "Shoulder pain", "Low impact only", "Asthma", "None"],
        default=["None"]
    )

    time_per_session = st.selectbox(
        "Typical session length",
        ["15-20 min", "30-45 min", "60+ min", "Varies"]
    )

    budget = st.select_slider(
        "Budget level", options=["Low", "Medium", "High"], value="Low"
    )

    liked_sports = st.multiselect(
        "Sports you like or want to try",
        ["Running", "Cycling", "Swimming", "Football", "Basketball", "Boxing",
         "Yoga", "Pilates", "Strength training", "HIIT", "VR Fitness"]
    )

    free_text = st.text_area("Tell us what you enjoy or prefer (free text)", height=100,
                             placeholder="e.g., short home workouts, no jumping, like music…")

    allow_vr = st.checkbox("I'm open to VR / gamified options")

    submitted = st.form_submit_button("Get recommendations")

# ----------------------  Layer Z (lite) engine  ----------------------
def infer_traits(data: Dict) -> Dict:
    """Rough intent inference from answers (Layer Z lite)."""
    t = {
        "wants_fat_loss": "Lose weight" in data["goal"],
        "wants_muscle": "Build muscle" in data["goal"],
        "wants_endurance": "Improve endurance" in data["goal"],
        "wants_flex": "Flexibility & mobility" in data["goal"],
        "wants_fun_vr": "Fun / gamified (VR)" in data["goal"] or data.get("allow_vr"),
        "intensity": data["intensity"],               # Low/Moderate/High
        "is_social": data["social"] in ("Duo/Partner", "Team"),
        "pref_outdoor": "Outdoor" in data["place"],
        "pref_home": "Home" in data["place"],
        "pref_gym": "Gym" in data["place"],
        "has_pool": ("Pool" in data["place"]) or ("Pool access" in data["equipment"]),
        "has_weights": "Free weights" in data["equipment"],
        "has_bike": "Bike (indoor/outdoor)" in data["equipment"],
        "low_impact_only": ("Low impact only" in data["constraints"])
                           or ("Knee pain" in data["constraints"])
                           or ("Back pain" in data["constraints"]),
        "time_short": data["time_per_session"] in ("15-20 min",),
        "time_medium": data["time_per_session"] in ("30-45 min",),
        "time_long": data["time_per_session"] in ("60+ min",),
        "budget_low": data["budget"] == "Low",
        "budget_mid": data["budget"] == "Medium",
        "budget_high": data["budget"] == "High",
        "liked": set(data["liked_sports"]),
        "free_text": data["free_text"].lower()[:500],
    }
    return t

SPORTS = [
    "Running", "Cycling", "Swimming", "Football", "Basketball", "Boxing",
    "Yoga", "Pilates", "Strength training", "HIIT", "VR Fitness"
]

def score_sports(traits: Dict) -> Dict[str, float]:
    s = {k: 0.0 for k in SPORTS}

    # Goals
    if traits["wants_fat_loss"]:
        for k in ["Running", "Cycling", "HIIT", "Boxing", "VR Fitness"]:
            s[k] += 2.0
    if traits["wants_muscle"]:
        s["Strength training"] += 3.0
        s["Boxing"] += 1.0
    if traits["wants_endurance"]:
        for k in ["Running", "Cycling", "Swimming"]:
            s[k] += 2.5
    if traits["wants_flex"]:
        for k in ["Yoga", "Pilates"]:
            s[k] += 3.0

    # Context
    if traits["pref_outdoor"]:
        s["Running"] += 1.5
        s["Cycling"] += 1.5
        s["Football"] += 1.0
        s["Basketball"] += 1.0

    if traits["pref_home"]:
        for k in ["Strength training", "Yoga", "Pilates", "HIIT", "VR Fitness"]:
            s[k] += 1.5

    if traits["pref_gym"]:
        s["Strength training"] += 1.5
        s["Swimming"] += 1.0

    if traits["has_pool"]:
        s["Swimming"] += 3.0
    if traits["has_weights"]:
        s["Strength training"] += 2.0
    if traits["has_bike"]:
        s["Cycling"] += 2.0

    # Intensity
    if traits["intensity"] == "High":
        for k in ["HIIT", "Boxing", "Running", "Basketball"]:
            s[k] += 1.0
    if traits["intensity"] == "Low":
        for k in ["Yoga", "Pilates", "Swimming"]:
            s[k] += 1.0

    # Constraints (low impact)
    if traits["low_impact_only"]:
        for k in ["Running", "HIIT", "Football", "Basketball", "Boxing"]:
            s[k] -= 3.0
        for k in ["Swimming", "Yoga", "Pilates", "Cycling"]:
            s[k] += 2.0

    # Time
    if traits["time_short"]:
        for k in ["HIIT", "VR Fitness", "Strength training", "Yoga"]:
            s[k] += 1.0
    if traits["time_long"]:
        for k in ["Cycling", "Football", "Basketball", "Running"]:
            s[k] += 1.0

    # Budget
    if traits["budget_low"]:
        for k in ["Running", "Yoga", "HIIT"]:
            s[k] += 0.7
    if traits["budget_high"] and traits["has_pool"]:
        s["Swimming"] += 0.7

    # Likes nudge
    for liked in traits["liked"]:
        s[liked] += 1.2

    # Free-text quick keywords
    txt = traits["free_text"]
    if any(w in txt for w in ["home", "apartment", "no equipment"]):
        for k in ["Yoga", "Pilates", "HIIT", "VR Fitness"]:
            s[k] += 0.8
    if any(w in txt for w in ["knee", "low impact", "rehab"]):
        for k in ["Swimming", "Yoga", "Cycling", "Pilates"]:
            s[k] += 1.0
        for k in ["Running", "HIIT"]:
            s[k] -= 1.0

    # VR openness
    if traits["wants_fun_vr"]:
        s["VR Fitness"] += 2.0

    return s

def top_recommendations(scores: Dict[str, float], k: int = 3) -> List[Tuple[str, float]]:
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

def vr_recommendation_needed(traits: Dict, top3: List[Tuple[str, float]]) -> bool:
    return traits["wants_fun_vr"] or (traits["pref_home"] and traits["time_short"])

def explain_choice(sport: str, traits: Dict) -> str:
    reasons = []
    if sport in ("Running", "Cycling", "Swimming"):
        if traits["wants_endurance"]: reasons.append("builds endurance")
        if traits["wants_fat_loss"]: reasons.append("great for fat loss")
    if sport == "Strength training":
        if traits["wants_muscle"]: reasons.append("best for muscle gain")
        if traits["pref_home"]: reasons.append("easy to do at home with basics")
    if sport in ("Yoga", "Pilates"):
        if traits["wants_flex"]: reasons.append("improves mobility & flexibility")
        if traits["low_impact_only"]: reasons.append("low impact friendly")
    if sport == "HIIT":
        if traits["time_short"]: reasons.append("effective in short time")
    if sport == "VR Fitness":
        reasons.append("fun & gamified; great adherence")
    txt = ", ".join(reasons) if reasons else "fits your preferences"
    return f"{sport}: {txt}."

# --------------------------  Results  --------------------------
if submitted:
    data = {
        "goal": goal,
        "intensity": intensity,
        "social": social,
        "place": place,
        "equipment": equipment,
        "constraints": constraints,
        "time_per_session": time_per_session,
        "budget": budget,
        "liked_sports": liked_sports,
        "free_text": free_text,
        "allow_vr": allow_vr,
        "lang": lang,
    }

    traits = infer_traits(data)
    scores = score_sports(traits)
    top3 = top_recommendations(scores, k=3)

    st.subheader("Your top matches")
    for name, sc in top3:
        st.markdown(f"- *{name}*  (score: {sc:.1f}) — {explain_choice(name, traits)}")

    if vr_recommendation_needed(traits, top3):
        st.info("Bonus option: *VR Fitness* (Beat Saber, Supernatural, Les Mills XR). "
                "Great if you want short, fun home sessions.")

    # Save light log (optional)
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/quiz_results.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"answers": data, "top3": top3}) + "\n")
    except Exception:
        pass

    st.divider()
    st.subheader("Not satisfied? Refine")
    user_refine = st.text_input("Describe what you want (free):",
                                placeholder="e.g., at home, 20 minutes, no jumping, competitive…")
    if st.button("Refine suggestions"):
        new_top = top3

        if USE_AI and openai_client:
            try:
                prompt = (
                    "User wants a refined sport recommendation based on previous picks and this extra note:\n"
                    f"{user_refine}\n\n"
                    "Return ONLY a JSON array of 3 sports. No text."
                )
                msg = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a sport-matching assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                import json as _json
                arr = _json.loads(msg.choices[0].message.content.strip())
                new_top = [(x, scores.get(x, 0.0)) for x in arr][:3]
            except Exception:
                # fallback to heuristic if AI fails
                pass

        if not USE_AI or not new_top or user_refine:
            # quick heuristic rewrite
            txt = user_refine.lower()
            boost = []
            if "home" in txt: boost += ["Yoga", "Pilates", "Strength training", "VR Fitness", "HIIT"]
            if "outdoor" in txt: boost += ["Running", "Cycling", "Football", "Basketball"]
            if "no jump" in txt or "low impact" in txt or "knee" in txt:
                boost += ["Swimming", "Yoga", "Cycling", "Pilates"]
            if "competitive" in txt or "team" in txt:
                boost += ["Football", "Basketball", "Boxing"]
            # apply boost
            for b in boost:
                scores[b] = scores.get(b, 0) + 1.2
            new_top = top_recommendations(scores, 3)

        st.markdown("### Refined picks")
        for name, sc in new_top:
            st.markdown(f"- *{name}*  (score: {sc:.1f}) — {explain_choice(name, traits)}")

    st.success("Done. You can tweak answers above and resubmit anytime.")
else:
    st.info("Fill the quiz and press *Get recommendations*.")
