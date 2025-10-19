---

### ⚙️ `PRPs/ai_docs/prp_hybrid_recommendation.md`

```md
# ⚙️ PRP: Hybrid Recommendation System  
*(English + Arabic Integrated Version)*

## 🎯 Purpose
Defines how Claude Code maintains the **hybrid retrieval flow**:
1. Knowledge Base (KB)  
2. Candidate Selector  
3. Hybrid Reasoner  
4. LLM Fallback  

This ensures recommendations are **consistent, explainable, and non-repetitive.**

---
## 🇬🇧 English Guidelines
Claude should:
- Keep `hybrid_recommend` callable and never overwritten by import fallbacks.  
- Maintain stable scoring logic in `candidate_selector.py`:
  ```python
  score = prior + Σ (trait_strength × trait_weight) + intent_boosts
