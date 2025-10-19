# 🧠 PRP: Layer-Z Deep Analysis Context  
*(English + Arabic Integrated Version)*  

## 🎯 Purpose  
This PRP defines how Claude should interpret and process the **Layer-Z system** — the "Silent Engine" behind SportSync AI.  
It teaches the model to reason about **inner motivations, unconscious flow triggers, and deep personality traits** before suggesting any sport or identity.

---
## 🇬🇧 English Context
When analyzing user answers or traits:
- Prioritize “unspoken” cues (flow, obsession, quiet motivation).  
- Detect **hidden intentions** using the Layer-Z question set.  
- Cross-link these with personality axes and contextual intents (VR/Non-VR).  
- Output structured insights that explain *why* a certain sport fits the user’s **core identity**, not just their hobbies.  

Example reasoning snippet:
```python
if z_signals.get("focus_seeker") and z_signals.get("anxious") < 0.4:
    recommendation_weight["archery_vr"] += 0.25
