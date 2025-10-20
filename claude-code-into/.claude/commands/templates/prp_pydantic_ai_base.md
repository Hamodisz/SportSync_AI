# PRP — Pydantic AI Base (All-in-One) — SportSync / Claude Code (VS Code)

> **Single file** that contains EVERYTHING: validation loop (all levels), schemas, context rules, examples, and deployment checklist.  
> Save as: `PRPs/templates/prp_pydantic_ai_base.md`

---

## ⚙️ Run
```bash
# from repo root (VS Code terminal)
bash -lc '
set -euo pipefail
echo "🏁 SportSync — Full PRP Validation"

# ─────────────────────────────────────────────────────────
# LEVEL 1: Project & Structure Validation
# ─────────────────────────────────────────────────────────
echo "🔍 L1: Structure"
tree -a -I ".git|.venv|__pycache__|node_modules" || true

req_logic=(core backend_gpt.py memory_cache.py user_logger.py)
req_analysis=(layer_z_engine.py)
req_core=(hybrid.py llm_client.py app_config.py security.py data_pipe.py)
req_data=(data data/sportsync_knowledge.json data/labels_aliases.json data/blacklist.json)

check_file(){ test -e "$1" && echo "✅ $1" || echo "❌ MISSING: $1"; }
for f in "${req_logic[@]}"; do check_file "logic/$f"; done
for f in "${req_analysis[@]}"; do check_file "analysis/$f"; done
for f in "${req_core[@]}"; do check_file "core/$f"; done
for f in "${req_data[@]}"; do check_file "$f"; done

# Quick imports presence
grep -ERq "from pydantic import BaseModel" || echo "⚠️ pydantic BaseModel not referenced"
grep -ERq "def generate_sport_recommendation" logic || echo "⚠️ generate_sport_recommendation not found"
grep -ERq "def hybrid_recommend" core logic || echo "⚠️ hybrid_recommend not found"

# ─────────────────────────────────────────────────────────
# LEVEL 2: Runtime Smoke (Backend + Hybrid)
# ─────────────────────────────────────────────────────────
echo "⚙️ L2: Runtime smoke"
python - <<PY
import json
try:
    from core.hybrid import hybrid_recommend
    print("✅ import core.hybrid.hybrid_recommend")
except Exception as e:
    print("❌ hybrid import:", e)

try:
    from logic.backend_gpt import generate_sport_recommendation
    print("✅ import logic.backend_gpt.generate_sport_recommendation")
    ans={"goals":"هدوء وتركيز","likes":["ألغاز","VR"],"style":"فردي"}
    cards=generate_sport_recommendation(ans, lang="العربية")
    print("Cards:", len(cards))
    for i,c in enumerate(cards[:3],1):
        print(f"—[{i}] {str(c)[:120]}{'…' if len(str(c))>120 else ''}")
except Exception as e:
    print("❌ backend call:", e)
PY

# ─────────────────────────────────────────────────────────
# LEVEL 3: Layer-Z / Signals Consistency
# ─────────────────────────────────────────────────────────
echo "🧠 L3: Layer-Z"
python - <<PY
try:
    from analysis.layer_z_engine import analyze_silent_drivers, analyze_user_intent
    a={"q1":"أحب الألغاز والتحليل","q2":"أفضل اللعب الفردي بهدوء","q3":"VR ممتع"}
    sd = analyze_silent_drivers(a, lang="العربية")
    it = analyze_user_intent(a, lang="العربية") if "analyze_user_intent" in globals() else []
    print("silent_drivers:", sd)
    print("intents:", it)
    assert isinstance(sd, (list,tuple)), "silent_drivers must be list-like"
    print("✅ Layer-Z signals ok")
except Exception as e:
    print("❌ Layer-Z:", e)
PY

# ─────────────────────────────────────────────────────────
# LEVEL 4: Schema Validation (Pydantic)
# ─────────────────────────────────────────────────────────
echo "📘 L4: Pydantic schemas"
python - <<PY
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError, conint, constr

Lang = constr(pattern=r"^(العربية|ar|en)$")

class RecommendReq(BaseModel):
    user_id: constr(min_length=1) = "web_user"
    lang: Lang = "العربية"
    answers: Dict[str, Any]

class SportCard(BaseModel):
    sport_label: constr(min_length=3)
    what_it_looks_like: constr(min_length=30)
    inner_sensation: constr(min_length=10)
    why_you: constr(min_length=10)
    first_week: constr(min_length=10)
    progress_markers: Optional[str] = None
    win_condition: Optional[str] = None
    core_skills: List[constr(min_length=2)] = []
    mode: constr(min_length=3) = "Solo/Team"
    variant_vr: constr(min_length=5)
    variant_no_vr: constr(min_length=5)
    difficulty: conint(ge=1, le=5) = 2
    source: constr(min_length=2) = "KB"

class RecommendRes(BaseModel):
    cards: List[SportCard]

# minimal sample
try:
    sample = RecommendRes(cards=[SportCard(
        sport_label="Tactical Immersive Combat",
        what_it_looks_like="ساحة محاكاة آمنة مع قراءة زوايا وتبديل إيقاع وقرار خاطف بدون ذكر وقت/تكلفة/مكان.",
        inner_sensation="هدوء عصبي مع يقظة ذهنية.",
        why_you="تكره التكرار وتميل للتفكير التكتيكي.",
        first_week="ثبّت إيقاعك وجرّب ظهور/انسحاب قصير.",
        progress_markers="وضوح قرار، سلاسة حركة",
        win_condition="إنجاز المهمة دون انكشاف.",
        core_skills=["قراءة زاوية","تبديل إيقاع","قرار سريع"],
        mode="فردي/جماعي",
        variant_vr="نسخة VR تركّز على تتبّع الزوايا.",
        variant_no_vr="عوائق خفيفة ومسارات ظلّ.",
        difficulty=3,
        source="LLM"
    )])
    print("✅ Pydantic schemas ok; sample validated")
except ValidationError as e:
    print("❌ Schema invalid:\n", e)
PY

# ─────────────────────────────────────────────────────────
# LEVEL 5: Policy / Content Guards (no time/cost/place/equipment)
# ─────────────────────────────────────────────────────────
echo "🛡️ L5: Policy guards"
python - <<PY
import re, json
from pathlib import Path
pat=r"(\\b\\d+\\s*(?:دقيقة|دقائق|ثانية|ساعة|min|hour|set|rep|budget|cost)\\b|بالبيت|في\\s*البيت|نادي|جيم|gym|\\$|€)"
for p in Path("data").glob("**/*.json"):
    try:
        t=p.read_text("utf-8")
        if re.search(pat, t, flags=re.IGNORECASE):
            print("⚠️ Guard hit in", p)
    except Exception: pass
print("✅ Guard scan finished")
PY

# ─────────────────────────────────────────────────────────
# LEVEL 6: Global Dedupe / Blacklist Snapshot
# ─────────────────────────────────────────────────────────
echo "🧾 L6: Blacklist snapshot"
python - <<PY
import json, os
from pathlib import Path
BL=Path("data/blacklist.json")
if BL.exists():
    js=json.loads(BL.read_text("utf-8"))
    print("labels:", len((js or {}).get("labels", {})))
else:
    print("ℹ️ no blacklist yet")
PY

echo "🎯 All levels executed."
'

🧩 Context Engineering Rules (SportSync)
	•	Pipeline: Evidence Gate → Analysis (Layer-Z) → KB → Hybrid → LLM (fallback)
	•	Always produce 3 clear sport-identity cards.
	•	Remove references to time/cost/location/equipment/sets/reps.
	•	Enforce meaningful sections: what_it_looks_like, inner_sensation, why_you, first_week, win_condition, core_skills, variant_vr, variant_no_vr.
	•	Arabic default; accept "العربية" | "ar" | "en".
	•	Brand footer: — Sports Sync.

📚 Examples (prompts to Claude)
	•	Tasking
Build hybrid candidate selector using traits: precision, calm_regulation, tactical_mindset, vr_inclination. Expose select_top(traits,intents,k,guards) and unit tests.
	•	Refactor
Move blacklist I/O into core/blacklist_io.py with thread-safe file locks and atomic writes.
	•	Guard Fix
Strengthen _GENERIC_LABEL_RE and add _label_is_generic() unit tests for Arabic/English.

🚀 Deployment Checklist
	•	PRP validation ✅
	•	Unit tests pytest -q ✅
	•	data/last_run.json snapshot ✅
	•	No guard violations ✅
	•	Commit & push ✅
	•	Deploy (Render/RunPod) ✅

End of single-file PRP
