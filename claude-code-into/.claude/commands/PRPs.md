# 🧠 PRPs — Context Engineering Guide for Claude Code  
*(For use inside VS Code with SportSync AI)*

---

## 🎯 Purpose
This file defines **Prompt Reasoning Patterns (PRPs)** for Claude Code.  
It helps the model:
- Understand **SportSync AI’s unique reasoning layers** (Layer-Z, hybrid, fallback, memory).  
- Respond in a **developer-aware**, structured, and reproducible way.  
- Always operate within the **context of the repository** (not a general chat).  

---

## 🧩 General Prompt Rules

1. **Always ground reasoning** in project context (`CLAUDE.md`, `README.md`, code files).  
2. Use the `tree` command or quick read of `.py` and `.json` files before editing.  
3. Keep your chain-of-reasoning internal — show *only conclusions*, not internal thought.  
4. Prefer full-file patches (`*** Begin Patch`) instead of fragmented changes.  
5. When unsure, run diagnostic steps:
   - `grep` or `find` relevant files.
   - summarize findings briefly.
6. Always check if the change affects:
   - `memory_cache`
   - `user_logger`
   - `backend_gpt` recommendation order (KB → Hybrid → LLM fallback).

---

## ⚙️ Prompt Patterns

### 🧱 1. Structural Understanding
**When:** Exploring unfamiliar parts of the project.  
**Prompt Example:**
#____________
Explain the purpose and relationship between core/backend_gpt.py and logic/retrieval/candidate_selector.py.
Focus on: data flow, fallback order, and interaction with memory_cache.

✅ Expected Output:
- Summary of both files.
- Diagram-style bullet flow.
- One insight line on performance or redundancy.

---

### 🧠 2. Contextual Refactor
**When:** You need cleaner, more modular code.  
**Prompt Example:**
#____________
Refactor core/backend_gpt.py to ensure hybrid_recommend is not overwritten by imports.
Preserve LLM fallback logic and confirm all three recommendation paths (standard, alternative, creative) are still returned.

✅ Expected Output:
- Single cohesive patch with `*** Begin Patch` + `*** End Patch`.
- Inline comments only if non-obvious.
- Maintain encoding header and docstring.

---

### 🔍 3. Deep Reasoning Repair
**When:** The logic “works” but behaves wrongly (e.g. repeating same sport).  
**Prompt Example:**
#___________
Analyze backend_gpt.py and candidate_selector.py to find why all recommendations are identical.
Identify if the fallback_identity is triggered too early or KB selection fails.
Then patch the fix directly.

✅ Expected Output:
- Short diagnostic summary.
- Full fixed code block.
- Explanation of what caused the issue and how it’s resolved.

---

### 💬 4. Prompt Chain Testing
**When:** You want to verify Claude’s reasoning matches user-facing tone.  
**Prompt Example:**

#____________
Simulate a dynamic chat response in Arabic for a user who scored high in calm_regulation and tactical_mindset.
The response should feel emotional, not mechanical.
Avoid repeating labels and preserve brand tone.

✅ Expected Output:
- Markdown snippet of expected chat reply.
- Followed by a note on how to inject this tone into `dynamic_chat.py`.

---

### ⚡ 5. Layer-Z Reasoning Context
**When:** Adjusting how the system interprets “silent drivers”.  
**Prompt Example:**

#____________
Add a mini Layer-Z filter that adjusts sport weighting based on ‘flow triggers’.
Implement in user_analysis.py with minimal disruption.
Show code + example of how a ‘focus seeker’ would be matched differently.

✅ Expected Output:
- Functional patch.
- Example JSON input/output.
- One-liner on how it interacts with hybrid_recommend.

---

### 🧩 6. Multilingual Handling
**When:** You’re working on Arabic/English logic layers.  
**Prompt Example:**

#___________
Ensure backend_gpt.py correctly detects language from answers and applies Arabic prompt system.
Show how _llm_fallback switches between sys_ar and sys_en.

✅ Expected Output:
- Verified language branch (ar/en).
- Inline note about UTF-8 and encoding safety.

---

### 📦 7. Testing / Debug Context
**When:** Running local validation with Claude’s permissions.  
**Prompt Example:**
#_________
Run Bash(pytest -q) to validate analysis_layers_1_40.py
If failed, explain the traceback and propose fix patches inline.

✅ Expected Output:
- Test results summary.
- Fix suggestion as code patch.
- No redundant text.

---

## 🧰 Developer Discipline Checklist

Before committing any Claude-generated change:
- [ ] Confirm `backend_gpt.py` still returns 3 distinct cards.  
- [ ] Run `ruff check .` — no lint errors.  
- [ ] Ensure no hardcoded API keys.  
- [ ] Update CLAUDE.md if new modules or layers are added.  
- [ ] Preserve Sports Sync signature in all AI-facing prompts.  

---

## 🔮 Example Context Loop (for Claude Code)

**Example Use Case:**
You open `core/backend_gpt.py` and ask:

#_____________
Claude, identify where fallback_identity is used and refactor it to ensure KB-first mode always precedes LLM fallback.
Preserve all docstrings and ensure consistent indentation.

Claude should:
1. Read the file.
2. Recognize the fallback logic section.
3. Apply reasoning using this PRPs.md.
4. Output a **clean patch** that’s context-aware and brand-consistent.

---

## 🧾 Notes
- The goal of this file is not to add rules, but to give Claude a *thinking framework*.  
- Treat this as the **cognitive skeleton** for autonomous coding.  
- You can extend this with custom PRPs (like “Marketing Agent Pattern”, “VR Mode Pattern”) later.

---

**End of PRPs.md — © SportSync AI Context Engineering Framework**
