# -*- coding: utf-8 -*-
"""
logic/retrieval/candidate_selector.py
------------------------------------
Selector بسيط يقرأ كتالوج الهويات الرياضية من JSON،
ويحسب سكور لكل عنصر حسب:
  score = prior + Σ (trait_strength * trait_weight) + intent_boosts

- يدعم حجب الـ high-risk لو فيه "anxious" عالية.
- ترتيب حتمي (stable) مع tie-break على label وindex.
- يرجّع قائمة مرتبة تنازليًا بالسكور مع حقول (id, label, score, reasons).

الاستخدام:
    from logic.retrieval.candidate_selector import select_top
    items = select_top(traits={"precision":0.9, "prefers_solo":1.0}, intents=["VR"], k=5)
"""

from __future__ import annotations
import json, os, re
from typing import Any, Dict, List, Tuple
from pathlib import Path
from datetime import datetime

CATALOG_PATH = os.getenv("SPORTS_CATALOG_PATH", "data/sports_catalog.json")

# ---------- utils ----------
_AR_DIAC_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
_AR_MAP = str.maketrans({"أ":"ا","إ":"ا","آ":"ا","ؤ":"و","ئ":"ي","ة":"ه","ى":"ي"})
def _normalize_ar(t: str) -> str:
    if not isinstance(t, str): t = str(t or "")
    t = _AR_DIAC_RE.sub("", t).translate(_AR_MAP)
    return re.sub(r"\s+", " ", t).strip().lower()

def _canon_label(label: str) -> str:
    lab = _normalize_ar(label)
    lab = re.sub(r"[^a-z0-9\u0600-\u06FF]+", " ", lab)
    return re.sub(r"\s+", " ", lab).strip(" -—:،")

def _load_catalog(path: str = CATALOG_PATH) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Catalog not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data.get("items"), list):
        raise ValueError("Catalog JSON must have a top-level 'items' list.")
    return data

def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

# ---------- core scoring ----------
def _item_score(
    item: Dict[str, Any],
    traits: Dict[str, float],
    intents: List[str],
    guards: Dict[str, Any],
) -> Tuple[float, List[str]]:
    """
    يحسب سكور عنصر واحد ويعيد (score, reasons)
    """
    prior = _safe_float(item.get("prior", 0.0))
    tw: Dict[str, float] = {k: _safe_float(v) for k, v in (item.get("trait_weights") or {}).items()}
    score = prior
    reasons: List[str] = []
    # traits contribution
    for t_name, t_strength in (traits or {}).items():
        w = tw.get(t_name, 0.0)
        if w:
            contrib = float(t_strength) * float(w)
            score += contrib
            reasons.append(f"{t_name}×{w:+.2f}")
    # intent boosts (optional)
    if intents:
        ib: Dict[str, float] = {k.lower(): _safe_float(v) for k, v in (item.get("intent_boosts") or {}).items()}
        for it in intents:
            b = ib.get(str(it).lower(), 0.0)
            if b:
                score += b
                reasons.append(f"intent:{it}+{b:+.2f}")
    # guards: anxiety vs risk
    anxious = float(traits.get("anxious", 0.0))
    avoid_high = bool(guards.get("avoid_high_risk_for_anxiety", True))
    if avoid_high and anxious >= 0.8 and str(item.get("risk_level","")).lower() == "high":
        score += -1e6
        reasons.append("blocked:high_risk_anxiety")
    return score, reasons

def rank_candidates(
    traits: Dict[str, float],
    intents: List[str] | None = None,
    guards: Dict[str, Any] | None = None,
    path: str = CATALOG_PATH,
) -> List[Dict[str, Any]]:
    """
    يرجّع كل العناصر مع سكور مرتّبة تنازليًا.
    """
    intents = intents or []
    guards = guards or {}
    data = _load_catalog(path)
    items: List[Dict[str, Any]] = data["items"]

    ranked: List[Tuple[float, int, Dict[str, Any], List[str]]] = []
    for idx, it in enumerate(items):
        sc, rs = _item_score(it, traits, intents, guards)
        ranked.append((sc, idx, it, rs))

    # ترتيب حتمي: السكور تنازلي، إن تعادل → prior أعلى، بعدها label canonical، بعدها index
    def _sort_key(row):
        sc, idx, it, _ = row
        label = _canon_label(it.get("label",""))
        prior = _safe_float(it.get("prior", 0.0))
        return (-sc, -prior, label, idx)

    ranked.sort(key=_sort_key)

    out: List[Dict[str, Any]] = []
    for rank, (sc, idx, it, rs) in enumerate(ranked, start=1):
        out.append({
            "rank": rank,
            "id": it.get("id"),
            "label": it.get("label"),
            "score": float(f"{sc:.6f}"),
            "prior": _safe_float(it.get("prior", 0.0)),
            "risk_level": it.get("risk_level", "unknown"),
            "reasons": rs,
            "aliases": it.get("aliases", []),
        })
    return out

def select_top(
    traits: Dict[str, float],
    intents: List[str] | None = None,
    k: int = 8,
    guards: Dict[str, Any] | None = None,
    path: str = CATALOG_PATH,
) -> List[Dict[str, Any]]:
    """
    يختار أعلى k عناصر (مرتبة) مع السكور وأسباب مختصرة.
    """
    ranked = rank_candidates(traits=traits, intents=intents, guards=guards, path=path)
    return ranked[: max(0, int(k))]

# ---------- CLI quick check ----------
if __name__ == "__main__":
    sample_traits = {
        "precision": 0.9,
        "prefers_solo": 1.0,
        "tactical_mindset": 0.7,
        "anxious": 0.2,
        "vr_inclination": 0.6,
        "likes_puzzles": 0.5,
    }
    sample_intents = ["VR", "تخفّي"]
    sample_guards = {"avoid_high_risk_for_anxiety": True}
    top = select_top(sample_traits, sample_intents, k=5, guards=sample_guards)
    print(json.dumps(top, ensure_ascii=False, indent=2))
