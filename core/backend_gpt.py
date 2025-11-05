# -- coding: utf-8 --
"""Rich analytical fallback recommendations for SportSync - WITH SPORT INVENTION."""
from __future__ import annotations

if __name__ == '__main__':  # allow running as script
    import sys
    from pathlib import Path as _Path
    sys.path.append(str(_Path(__file__).resolve().parent.parent))

import hashlib
import json
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence, Optional, Tuple

try:  # Optional LLM client; fallback works without it.
    from core.llm_client import make_llm_client, pick_models, chat_once  # type: ignore
    from core.dual_model_client import (  # type: ignore
        analyze_user_with_discovery,
        invent_sport_identities_with_reasoning
    )
    from core.sport_identity_generator import get_sport_identity_generator  # type: ignore
    DUAL_MODEL_ENABLED = True
    SPORT_INVENTOR_ENABLED = True
except Exception:  # pragma: no cover - LLM unavailable
    make_llm_client = None
    pick_models = None
    chat_once = None
    analyze_user_with_discovery = None
    invent_sport_identities_with_reasoning = None
    get_sport_identity_generator = None
    DUAL_MODEL_ENABLED = False
    SPORT_INVENTOR_ENABLED = False

from core.user_logger import log_event, log_recommendation_result


LLM_CLIENT: Optional[Any]
CHAT_MODEL: str
CHAT_MODEL_FALLBACK: str

if make_llm_client is not None:
    try:
        LLM_CLIENT = make_llm_client()
    except Exception:
        LLM_CLIENT = None
else:
    LLM_CLIENT = None

if pick_models is not None:
    try:
        CHAT_MODEL, CHAT_MODEL_FALLBACK = pick_models()
    except Exception:
        CHAT_MODEL, CHAT_MODEL_FALLBACK = ("", "")
else:
    CHAT_MODEL = ""
    CHAT_MODEL_FALLBACK = ""

# Updated banned terms - we want creativity, not diet/weight focus
BANNED_TERMS = [
    "خسارة الوزن", "حرق الدهون", "سعرات", "وزن",  
    "خطة أسبوعية", "دقيقة", "دقائق", "ساعة", "ساعات",
    "كرة القدم", "كرة السلة", "سباحة عادية", "ركض عادي"  # Ban traditional sports
]

ARACHETYPE_DATA: Dict[str, Dict[str, Any]] = {}
LAST_RECOMMENDER_SOURCE = "sport_inventor_v2"  # Updated source


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[\w\u0600-\u06FF]+", text.lower())


def _jaccard(a: str, b: str) -> float:
    set_a = set(_tokenize(a))
    set_b = set(_tokenize(b))
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _stable_json(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(data)
