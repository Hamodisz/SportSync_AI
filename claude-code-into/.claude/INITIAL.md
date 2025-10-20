# INITIAL.md — SportSync AI (Context Boot File)

## FEATURE:
Build a contextual intelligence engine for **SportSync AI** — a personalized sport identity system powered by Pydantic + AI Agents.  
The agent analyzes user traits, intentions (Layer Z), and preferences, then recommends matching sport identities — with optional VR/AR pathways.

## EXAMPLES:
- examples/basic_trait_agent — Basic trait analyzer using stored user sessions
- examples/layer_z_agent — Deep intent recognition agent (Silent Engine)
- examples/retrieval_agent — Connects to `logic/retrieval/candidate_selector.py` for KB-based sport ranking
- examples/hybrid_agent — Merges KB + LLM recommendations for hybrid identity inference
- examples/vr_exp_agent — Generates VR/No-VR activity variants based on difficulty
- examples/testing_suite — Integration tests for recommendation consistency

## DOCUMENTATION:
Use these docs and PRPs to keep Claude aware of project context.

- Pydantic AI Official Docs: https://ai.pydantic.dev/
- SportSync AI Vision: *"SportSync redefines how humans connect with movement by uncovering their innate sport identity."*
- Core Architecture: `logic/backend_gpt.py`, `logic/dynamic_chat.py`, `logic/shared_utils.py`
- Personality & Memory: `memory_cache.py`, `user_logger.py`
- Analysis Layers Reference: `analysis/layer_z_engine.py` and `analysis_layers_1_141.py`
- Brand Signature: `brand_signature.py`
- Recommended Workflow:  
  1. Run `tree` to map the repo  
  2. Read `CLAUDE.md` → `README.md` → `PRPs/ai_docs/`  
  3. Summarize structure, dependencies, and current pipeline

## OTHER CONSIDERATIONS:
- **Security:** Never expose raw user data; anonymize session IDs before saving.
- **Performance:** Cache analysis with `memory_cache.save_cached_analysis()` before LLM calls.
- **AI Models:** Prefer local KB first → hybrid → LLM fallback; avoid repeating identical recommendations.
- **VR Integration:** Always produce both `variant_vr` and `variant_no_vr` in sport cards.
- **Testing:**  
  - Unit: verify analysis layer outputs.  
  - Integration: ensure 3 distinct recommendations (standard + alternative + creative).  
  - Regression: confirm consistent identity ranking from `candidate_selector`.
- **Prompt Design:** Keep Claude prompts emotion-aware; avoid words like *time, cost, gear, place*.
- **Context Engineering:** Use `PRPs/ai_docs/` to store new context PRPs after major updates.
- **Agents:**  
  - `content_creator_agent` → generates shareable sport identity stories.  
  - `feedback_analyzer` → monitors user engagement and refines recommendations.  
  - `brand_guardian` → ensures SportSync voice and emotional tone.

## RELEVANT URLS:
- SportSync AI Docs: https://sportsync.ai/docs  
- Pydantic AI: https://ai.pydantic.dev/  
- Anthropic Claude Code Guide: https://docs.anthropic.com/claude-code  
- Streamlit Integration: https://docs.streamlit.io/  
- OpenAI Python SDK: https://github.com/openai/openai-python

---

### INTERNAL NOTES
When Claude Code starts, it should:
1. Read `CLAUDE.md` to load project context.  
2. Identify this file as the kickoff guide.  
3. Confirm understanding of SportSync AI’s goal and architecture.  
4. Generate or update tasks under `.claude/commands/` accordingly.

---

> **Mission Summary:**  
> SportSync AI isn’t just recommending sports — it’s uncovering who the user *is* through motion, emotion, and mind flow.  
> Each recommendation must feel like a mirror of the user’s identity.
