---

### 💬 `PRPs/ai_docs/prp_dynamic_chat_context.md`

```md
# 💬 PRP: Dynamic Chat Personality Context  
*(English + Arabic Integrated Version)*

## 🎯 Purpose
Defines how Claude manages and expands `dynamic_chat.py` logic.  
It enables real conversational flow, memory linking, and emotional tone alignment.

---
## 🇬🇧 English Guidelines
Claude should:
- Preserve chat personality keys:

name, tone, style, philosophy

- Use previous session insights to generate adaptive prompts.
- Pause output if AI asks a question (`?` at the end).  
- Log all exchanges with:
```python
log_user_insight(type="chat_interaction", ...)

	•	Avoid repeating sport names; emphasize emotional resonance.

🧩 Example Prompt
User: "حسّيت أني أحب الهدوء أكثر من التحدي."
AI: "إذن يبدو أنك تنجذب لما يسمّى بالـ Flow Sports — أنشطة تذوب فيها ببطء، مثل الغوص أو التأمل الحركي. تحب أشرح لك نوعك الرياضي؟"
