# -- coding: utf-8 --
"""
core/recs/text_ops.py
---------------------
دوال معالجة نصوص عامة ومحايدة يمكن استخدامها في كل الوحدات بدون أي اعتماد
على قواعد/حراس أو إعدادات. تم تفكيكها من backend_gpt.py كما هي بدون اختصار.

تتضمن:
- _normalize_ar: تطبيع عربي (حذف التشكيل + توحيد بعض الحروف)
- _norm_text: تحويل أي قيمة (list/dict/tuple/None/number) إلى نص نظيف
- _clip: قص نص بعدد محارف مع إضافة … عند الحاجة
- _split_sentences: تقسيم نص إلى جمل
- _strip_code_fence: إزالة أسوار الأكواد ```...``` إن وجدت
- _tokenize: توليد توكنات (AR/EN) للاستخدام في التشابه
- _to_bullets: تحويل نص/قائمة/بُنى متداخلة إلى قائمة نقاط ثابتة

ملاحظات:
- هذا الملف لا يعتمد على أي متغيرات بيئية ولا على config_runtime أو rules.
- أي دوال لها علاقة بحظر الأسماء/الجمل أو القواعد سيتم وضعها في core/recs/rules.py.
"""

from __future__ import annotations

import json
import re
from typing import Any, List

# ========= Helpers: Arabic normalization =========
_AR_DIAC = r"[ًٌٍَُِّْـ]"

def _normalize_ar(t: str) -> str:
    """
    تطبيع نص عربي:
    - حذف التشكيل والمدود
    - توحيد (أ/إ/آ) -> ا ، (ة -> ه) ، (ى -> ي) ، (ؤ -> و) ، (ئ -> ي)
    - ضغط المسافات
    """
    if not t:
        return ""
    t = re.sub(_AR_DIAC, "", t)
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ؤ", "و").replace("ئ", "ي")
    t = t.replace("ة", "ه").replace("ى", "ي")
    t = re.sub(r"\s+", " ", t).strip()
    return t

# ========= Text normalizer (robust for list/dict inputs) =========
def _norm_text(val: Any) -> str:
    """
    حوّل أي نوع (list/dict/None/tuple/number) إلى نص نظيف.
    - القواميس: نحاول أخذ أحد المفاتيح (text/desc/value/answer)، وإلا نسلسل JSON
    - القوائم/التُبابيع: نفرد المحتوى ونفصله بـ "، "
    """
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, (list, tuple)):
        flat: List[str] = []
        for x in val:
            if isinstance(x, (list, tuple)):
                flat.extend(map(str, x))
            else:
                flat.append(str(x))
        return "، ".join([s.strip() for s in flat if s and str(s).strip()])
    if isinstance(val, dict):
        for k in ("text", "desc", "value", "answer"):
            if k in val and isinstance(val[k], str):
                return val[k]
        return json.dumps(val, ensure_ascii=False)
    return str(val)

def _clip(s: str, n: int) -> str:
    """
    قص نص إلى n محرف كحد أعلى، مع إرجاع … عند القص.
    """
    if not s:
        return ""
    s = s.strip()
    return s if len(s) <= n else (s[: max(0, n - 1)] + "…")

def _split_sentences(text: str) -> List[str]:
    """
    تقسيم النص إلى جمل تقريبية بالاعتماد على علامات الوقف الشائعة AR/EN.
    """
    if not text:
        return []
    # ملاحظة: نستخدم \n (حرف n اللاتيني) ليس النون العربية
    parts = re.split(r"(?<=[\.\!\?؟])\s+|[\n،]+", text)
    return [s.strip() for s in parts if s and s.strip()]

def _strip_code_fence(s: str) -> str:
    """
    إزالة أسوار الأكواد ```...``` أو ```json ... ``` مع المحافظة على المحتوى الداخلي.
    """
    if not s:
        return s
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s

def _tokenize(text: str) -> List[str]:
    """
    تحويل نص إلى توكنات (AR/EN) بعد التطبيع العربي الأساسي.
    - نحذف كل ما ليس حرف/رقم عربي/لاتيني
    - نحذف التوكنات القصيرة (<= 2)
    """
    if not text:
        return []
    t = _normalize_ar(text.lower())
    toks = re.split(r"[^a-zA-Z0-9\u0600-\u06FF]+", t)
    return [w for w in toks if w and len(w) > 2]

def _to_bullets(text_or_list: Any, max_items: int = 6) -> List[str]:
    """
    يرجّع دائمًا List[str] مهما كان الإدخال (string/list/tuple/dict/nested).
    - إذا دخل نص مفرد: نقسمه على (; . \n ،) وننظّف النقاط
    - نقيّد بعدد عناصر أقصاه max_items
    """
    out: List[str] = []

    def _flat_add(x: Any) -> None:
        if x is None:
            return
        if isinstance(x, (list, tuple, set)):
            for y in x:
                _flat_add(y)
            return
        if isinstance(x, dict):
            for k in ("text", "desc", "value", "answer", "label", "title"):
                if k in x and isinstance(x[k], str) and x[k].strip():
                    out.append(x[k].strip())
                    return
            out.append(json.dumps(x, ensure_ascii=False))
            return
        s = _norm_text(x).strip()
        if s:
            out.append(s)

    _flat_add(text_or_list)

    if len(out) == 1 and isinstance(text_or_list, str):
        raw = re.split(r"[;\n\.،]+", out[0])
        out = [i.strip(" -•\t ") for i in raw if i.strip()]

    out = out[:max_items]
    out = [str(i) for i in out if str(i).strip()]
    return out
