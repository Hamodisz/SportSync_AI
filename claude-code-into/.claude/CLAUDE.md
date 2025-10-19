CLAUDE.md — SportSync AI Rules

🧠 Project Awareness and Context Rules

SportSync AI is an intelligent system for discovering each person’s innate sport identity.
It combines psychological, behavioral, and physical analysis layers — including Layer-Z (Silent Engine) — to generate emotional, realistic, and creative sport recommendations.

Core Principles
	•	The system doesn’t recommend a sport, it reveals a sport identity.
	•	All recommendations must avoid mentions of time, cost, venue, or equipment.
	•	Every model or agent must preserve the brand tone: analytical, empathetic, and adaptive.
	•	The assistant acts as an AI co-developer, not a chat bot.
	•	Everything should include the brand signature: Sports Sync ©.

⸻

🧩 Code Structure Guidelines

Project is structured as a modular Python architecture:

core/
 ├── backend_gpt.py         → main recommendation engine (3-card system)
 ├── dynamic_chat.py        → interactive AI chat layer
 ├── shared_utils.py        → prompt builders & helper functions
 ├── user_logger.py         → logs all insights & chat history
 ├── memory_cache.py        → cached analysis/personality
 ├── analysis/              → 141 analysis layers + Layer-Z
 ├── agents/                → marketing + system AI agents
 ├── data/                  → CSV/JSON knowledge bases
 └── app.py                 → Streamlit UI (ChatGPT-style)

Rules
	•	Keep imports defensive (try/except) for cross-folder compatibility.
	•	Use absolute imports under the core namespace when possible.
	•	No circular imports — rely on shared_utils instead.
	•	Each file should be self-contained and lint-clean.

⸻

🧪 Testing Requirements
	•	Unit tests for each analysis layer in analysis/.
	•	Mock test for backend_gpt.generate_sport_recommendation returning 3 cards.
	•	Integration test for app.py simulating full user session.
	•	All tests must run via:

pytest -q


	•	No external API calls during CI; mock OpenAI/OpenRouter.

⸻

⚙️ Task Completion Workflow

When asked to fix, refactor, or add, follow this pattern:
	1.	Explain what’s broken or improved (1–2 lines max).
	2.	Apply change in a single patch block or full file snippet.
	3.	Include reasoning in comments only if non-obvious.
	4.	Never split output into multiple unrelated replies.

Format must follow the standard:

*** Begin Patch
*** Update File: core/backend_gpt.py
@@
- old code
+ new fixed code
*** End Patch



⸻

🎨 Style Conventions

Python
	•	Encoding: # -*- coding: utf-8 -*-
	•	Linting: ruff + black (line length 100)
	•	Typing: Full typing coverage (List, Dict, Optional, etc.)
	•	Docstrings: Google style
	•	Logging: _dbg, _warn, _err helpers only
	•	No prints, no raw exceptions

Streamlit
	•	User messages (Arabic or English) must respect direction and font.
	•	Dynamic chat uses real-time memory and Sports Sync persona.
	•	Use emoji headers for recommendation types:
	•	🟢 Primary (Realistic)
	•	🌿 Alternative
	•	🧠 Creative (Innovative)

⸻

📘 Documentation Standards

Each file must include a short header:

# -*- coding: utf-8 -*-
"""
File: backend_gpt.py
Module: Core Recommendation Engine
Description: Generates 3 sport identity recommendations
Author: Sports Sync AI Team
© Sports Sync
"""

	•	Update docstrings if function parameters change.
	•	Use inline comments only for non-obvious logic.
	•	Avoid duplicating documentation from other files.

⸻

✅ Commit & Review Standards

Commit format (Conventional Commits):

feat(core): add Layer-Z hybrid fallback
fix(app): correct language mismatch on load
refactor(shared): merge prompt builders

Pull request summary:

## What Changed
## Why
## Testing Evidence
## Rollback Plan

All code must be free of:
	•	TODOs without issue numbers
	•	Debug prints
	•	API keys or secrets (use .env)

⸻

🧩 Example Claude Behavior
	•	Understand full context of SportSync (Layer-Z, fallback logic, VR variants).
	•	When fixing code, ensure hybrid → LLM fallback order remains intact.
	•	When refactoring, do not break caching or user_logger links.
	•	Always validate that 3 recommendations are returned even if one layer fails.

⸻

🧠 Summary

This CLAUDE.md serves as:
	•	Memory + context for Claude Code or any AI dev tool
	•	Baseline for clean, modular, emotionally intelligent AI code
	•	Rulebook ensuring Sports Sync AI stays consistent, scalable, and explainable.
