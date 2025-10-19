SportSync — Layer-Z Sports Identity Recommender

SportSync turns short answers into three clear “sport-identity” cards, each with a qualitative first week, VR / no-VR variants, and a warm human tone.
It is Knowledge-Base-first (KB-first) and only uses an LLM as a fallback, with hard de-duplication, safety guards, and optional telemetry.


⸻

The Idea · The Goal · The Dream

Let’s say it plainly, with your voice: bold, clear, deep, future-oriented.

You’re not building “a fitness app.”
You’re not building “a cute AI.”

You’re building an intelligent system that uncovers a person’s true sport identity—even if it’s buried under 20 years of boredom, pressure, or fear of failure.

An AI that can tell someone:

“You’re not inactive because you’re lazy… you just haven’t met your true sport yet.”

🎯 Goal

Design AI that discovers each person’s innate sport—regardless of their style, mood, or past.
	•	Not “the sport that’s trending.”
	•	Not “the one that slims you down.”
	•	Not “one size fits all.”

The sport that fits you, and only you.

💡 What do we mean by “innate sport”? (real examples)
	•	Example 1
Hates the gym, hates crowds… but on a bike they disappear into themselves.
→ Not “cardio.” That’s Internal Escape.
→ The AI proposes: Bikepacking — Solitude Mode (an inventive cycling identity with mental maps and “escape routes”).
	•	Example 2
Loves dance, shy, hates competition, craves free breathing.
→ Not “Zumba.”
→ The AI proposes: Flow Dance Therapy (an expressive VR session with no audience).
	•	Example 3
Gamer, chaotic, but secretly loves order.
→ Not “CrossFit.”
→ The AI proposes: Combat Rhythm Sports (blending VR + tactical combat + lane sequencing).

⚙️ How it works (no fluff)
	1.	Ask ~20 smart questions (with Layer-Z that reveals deep drivers).
	2.	Analyze your profile across 141 layers (psychological, cognitive, environmental).
	3.	Fuse with a KB of 8,000+ sports (including obscure/experimental).
	4.	Then deliver:
	•	A realistic identity you could start tomorrow,
	•	A fallback if #1 doesn’t click,
	•	An inventive identity true to your makeup (non-traditional if needed).

💥 Why it matters
	•	People quit not because they’re weak—but because they’ve never seen themselves in the sport.
	•	Health systems treat sport as a class, not an identity.
	•	Millions burn cash on memberships and walk away after a week—no real match.

🎤 The dream, directly

“I want a system that lets anyone, anywhere discover the sport that feels innate—as if they were born with it.
An intelligent bridge between emotion and movement—willing to invent a new sport if it must.”

⸻

Features
	•	Evidence Gate
Rejects recommendations when answers are insufficient; asks 3 concise follow-ups first.
	•	KB-First Pipeline
Uses data/sportsync_knowledge.json (priors, trait_links, guards, label aliases, optional identities)
	•	ready-made templates per label → full cards without LLM.
	•	Layer-Z Alignment
Uses Z-axes (Calm/Adrenaline, Solo/Group, Technical/Intuitive), Z-intent keywords, and simple text signals.
	•	Three complete cards
sport_label, “what it looks like,” inner sensation, why you, first week (qualitative), progress markers, win condition, 3–5 core skills, mode, VR & no-VR variants, difficulty 1–5.
	•	Safety & wording rules
Hard filter to avoid time/cost/reps/sets/minutes/venues.
Optional: allow or mask sport names (allow_sport_names).
	•	Hard de-dup (local + global)
Uses data/blacklist.json to avoid repeats; generates variant labels when needed.
	•	Soft caching
Caches coach persona & recommendations for identical inputs.
	•	LLM as fallback
If KB can’t cover, call the LLM once + an optional repair round to improve alignment and completeness.

⸻

Screenshots

Add GIFs/images of your UI or sample cards here.

⸻

Quick Install

Requirements
	•	Python 3.10+
	•	OpenAI-compatible API key (only needed if LLM fallback is enabled)

git clone <YOUR_REPO_URL> sportsync
cd sportsync

python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt

Optional if you’ll use the LLM fallback:

# macOS/Linux
export OPENAI_API_KEY="sk-yourkey"
# Windows (PowerShell)
# setx OPENAI_API_KEY "sk-yourkey"


⸻

One-Liner Test

python -c "from core.backend_gpt import generate_sport_recommendation as g; print('\n\n'.join(g({'q1':'I prefer solo, calm play with precision aim','q2':'Open to trying VR'}, lang='English', user_id='demo')))"


⸻

Programmatic Usage

from core.backend_gpt import generate_sport_recommendation

answers = {
    "goal": "Tactical identity with quick wins and deep focus",
    "style": "Leaning calm & breath-led; mostly solo",
    "vr": "Curious to try VR later"
}

cards = generate_sport_recommendation(
    answers=answers,
    lang="English",      # or "العربية"
    user_id="user-123",  # used for caching/telemetry
    job_id="req-001"
)

print("\n\n---\n\n".join(cards))


⸻

Inputs & Outputs

Input (flexible dict)

Free-form keys with short, clear sentences.
Optional profile if you already encode axes/signals in your platform.

{
  "goal": "Calm identity with occasional snap decisions",
  "preference": "Solo, stealth/visual feints, precision/aim",
  "vr": "Maybe VR later",
  "profile": {
    "axes": {"calm_adrenaline": -0.6, "solo_group": -0.4, "tech_intuition": -0.3},
    "signals": ["precision","stealth"],
    "vr_inclination": 0.5
  }
}

Output

The function returns a list of 3 strings (cards). Each card contains:
	•	Sport label / identity
	•	What it looks like (scene)
	•	Inner sensation
	•	Why it fits you
	•	Core skills (3–5)
	•	Win condition
	•	First week (qualitative, no reps/sets/time/venue)
	•	VR and No-VR variants
	•	Approx difficulty 1–5

Content is scrubbed to avoid time, cost, reps/sets/minutes, or explicit venues.

⸻

Configuration & Environment

You can configure via environment variables or an optional core/app_config.py that exposes get_config().

Key environment variables
	•	OPENAI_API_KEY — required only if LLM fallback is used
	•	OPENAI_BASE_URL — alternate base (Azure/OpenRouter/…)
	•	OPENAI_ORG — optional org id
	•	CHAT_MODEL — main model (default: gpt-4o)
	•	CHAT_MODEL_FALLBACK — fallback model (default: gpt-4o-mini)
	•	REC_BUDGET_S — per-request time budget (default: 22)
	•	REC_REPAIR_ENABLED — enable repair round (default: 1)
	•	REC_FAST_MODE — shorten prompts & tokens (default: 0)
	•	REC_DEBUG — print debug logs (default: 0)
	•	MAX_PROMPT_CHARS — LLM prompt clipping (default: 6000)

Example get_config() return

{
  "llm": {"model": "gpt-4o"},
  "recommendations": {
    "allow_sport_names": true,
    "min_chars": 220,
    "require_win_condition": true,
    "min_core_skills": 3
  },
  "analysis": {
    "egate": {
      "min_answered": 3,
      "min_total_chars": 120,
      "required_keys": []  # e.g. ["goal","injury_history"]
    }
  },
  "security": {"scrub_urls": true}
}


⸻

Data Layout
	•	data/sportsync_knowledge.json
priors, trait_links, guards.high_risk_sports, z_intent_keywords, optional identities, label_aliases…
	•	data/labels_aliases.json
Canonicalization of label names & forbidden generic labels.
	•	data/blacklist.json
Updated automatically to prevent global label duplication across sessions.

If data files are missing, the engine still runs with internal fallbacks.

⸻

REST API (optional)

Minimal FastAPI server (server/main.py):

from fastapi import FastAPI
from pydantic import BaseModel
from core.backend_gpt import generate_sport_recommendation

app = FastAPI(title="SportSync API")

class Req(BaseModel):
    answers: dict
    lang: str = "English"
    user_id: str = "N/A"
    job_id: str = ""

@app.post("/recommend")
def recommend(req: Req):
    cards = generate_sport_recommendation(req.answers, req.lang, req.user_id, req.job_id)
    return {"cards": cards}

Run:

uvicorn server.main:app --host 0.0.0.0 --port 7860 --reload


⸻

Docker (optional)

Dockerfile

FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "7860"]

Build & run:

docker build -t sportsync .
docker run -it --rm -p 7860:7860 -e OPENAI_API_KEY="$OPENAI_API_KEY" sportsync


⸻

Troubleshooting & FAQ
	•	I get “OPENAI_API_KEY not set.”
Set the key or disable LLM fallback (KB-only still works with reduced coverage).
	•	Cards mention time/sets/venue.
They shouldn’t. Text is scrubbed; check custom templates and allow_sport_names plus filters in core/backend_gpt.py.
	•	Outputs feel repetitive.
data/blacklist.json prevents repeats globally. The engine also generates variant labels when necessary.
	•	I want stricter safety.
Add forbidden patterns to guards in the KB and adjust _FORBIDDEN_SENT.

⸻

Roadmap
	•	✅ KB-first pipeline, Evidence Gate, Layer-Z alignment, VR/no-VR variants
	•	⏳ Weighted evaluation & A/B telemetry for card quality
	•	⏳ UI with interactive “identity preview”
	•	⏳ Export cards to shareable images & short videos
	•	⏳ Native mobile client

⸻

License

MIT (see LICENSE).

⸻

Acknowledgements

Inspired by the clarity of projects like stable-diffusion-webui in keeping powerful systems simple to run and easy to extend.
