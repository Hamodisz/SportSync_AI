🔧 Debug Pattern

When Claude suspects fallback repetition:
_dbg("KB empty → switching to hybrid_recommend")

Then log source tags: "source": "KB" | "HYBRID" | "LLM"
---

### 🧩 `PRPs/ai_docs/prp_backend_logic.md`

```md
# 🧩 PRP: Backend Core Logic & Flow  
*(English + Arabic Integrated Version)*

## 🎯 Purpose
Guides Claude in editing or reasoning about `core/backend_gpt.py`.  
Focus: **consistency, language handling, and modular recommendation flow**.

---
## 🇬🇧 English Context
When editing backend:
1. Always keep encoding:  
   ```python
   # -*- coding: utf-8 -*-

	2.	Ensure generate_sport_recommendation() returns exactly 3 cards.
	3.	Never break the order:

KB → Hybrid → LLM

	4.	Use try/except safety blocks for all external modules:
	•	llm_client
	•	candidate_selector
	•	memory_cache
	5.	Save every run snapshot under /data/last_run.json.
