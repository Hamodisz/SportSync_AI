# -*- coding: utf-8 -*-
"""
LLM Client (Unified, Singleton, Rotating Models)
================================================
موحِّد الاتصال بنماذج OpenAI/Groq/OpenRouter (واجهة OpenAI المتوافقة).

المزايا:
- تحميل آمن لمفاتيح البيئة: .env ثم st.secrets (بدون الكتابة فوق env الموجود)
- ضبط base_url تلقائيًا (Groq/OpenRouter) + ترويسات OpenRouter
- اختيار موديلات بسلسلة (comma/newline/semicolon) مع تدوير تلقائي + remap للأسماء القديمة
- chat_once مع إعادة محاولات ذكية وإزالة penalties عند أخطاء 400
- Singleton + Lock لتفادي تكرار التهيئة (مع كاش اختياري لـ Streamlit)
- لوج نظيف يُطبع مرة واحدة عند تفعيل LLM_INIT_LOG=1

دوال التصدير الأساسية:
- make_llm_client()                    ← يبني عميل (مرة واحدة داخليًا عبر Singleton)
- make_llm_client_singleton()          ← يرجع عميل الـ Singleton مباشرة
- pick_models()                        ← يعيد (main_chain, fallback)
- get_models_cached()                  ← يعيد نفس (main_chain, fallback) مع كاش
- chat_once(client, messages, model, …)← مكالمة دردشة مع تدوير موديلات
- get_client_and_models()              ← (client, main_chain, fallback)
- get_streamlit_client()               ← عميل مع كاش Streamlit (إن وُجدت مكتبة streamlit)

ملاحظات:
- إن لم يوجد مفتاح API فالدوال التي تحتاج العميل سترفع RuntimeError، لكن بإمكان
  بقية النظام العمل على وضع KB-only بعد أن تتأكد من إرجاع None عند التهيئة اليدوية.
"""

from __future__ import annotations

import os
import re
import time
import random
import threading
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

# =========================
# Utilities & Logging
# =========================

def _log(msg: str) -> None:
    # لوج دائم للاستخدام الداخلي عند الحاجة
    print(f"[LLM_CLIENT] {msg}")

def _maybe_log_once(msg: str) -> None:
    # لوج اختياري (مرّة واحدة عادةً) بتفعيل LLM_INIT_LOG=1
    if os.getenv("LLM_INIT_LOG", "0") == "1":
        print(msg)

# =========================
# Bootstrap Environment
# =========================

def _bootstrap_env() -> None:
    """حمّل المفاتيح من .env و st.secrets بدون ما تكسّر أي قيم موجودة في env."""
    # 1) .env (محلي/كودسبيس/Render)
    try:
        from dotenv import load_dotenv  # type: ignore
        # جرّب جذور محتملة
        roots = [Path.cwd(), Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent]
        tried = set()
        for root in roots:
            env_path = (root / ".env").resolve()
            if env_path in tried:
                continue
            tried.add(env_path)
            if env_path.exists():
                load_dotenv(env_path, override=False)
                _maybe_log_once(f"[dotenv] loaded: {env_path}")
                break
    except Exception:
        pass

    # 2) st.secrets (Streamlit) — merge non-overriding
    try:
        import streamlit as st  # type: ignore
        secrets = dict(getattr(st, "secrets", {})) or {}
        def _pull(k: str):
            v = secrets.get(k)
            if v and not os.getenv(k):
                os.environ[k] = str(v)
        for k in (
            "GROQ_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY",
            "OPENAI_BASE_URL", "OPENROUTER_BASE_URL", "OPENAI_ORG",
            "OPENROUTER_REFERRER", "OPENROUTER_APP_TITLE",
            "CHAT_MODEL", "CHAT_MODEL_FALLBACK",
            "LLM_SEED",
        ):
            _pull(k)
        if secrets:
            _maybe_log_once("[secrets] streamlit.secrets merged into env (non-overriding).")
    except Exception:
        pass

_bootstrap_env()

# =========================
# OpenAI-compatible client
# =========================
try:
    # openai>=1.6,<2 المعيار الجديد (OpenAI class)
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore

# =========================
# Model Name Remapping
# =========================

_MODEL_REMAP: Dict[str, str] = {
    # أمثلة Groq قديمة → بدائل حيّة
    "llama3-70b-8192":            "llama-3.1-70b",
    "llama3-8b-8192":             "llama-3.1-8b-instant",
    "llama3-70b":                 "llama-3.1-70b",
    "llama3-8b":                  "llama-3.1-8b-instant",
    "llama-3.2-90b-text-preview": "llama-3.1-70b",
    "llama-3.1-70b-versatile":    "llama-3.1-70b",  # versatile تم إيقافه
    # شائعة في OpenRouter:
    "meta-llama/llama-3.1-70b-instruct:free": "meta-llama/llama-3.1-70b-instruct",
    "mistralai/mixtral-8x7b:free":            "mistralai/mixtral-8x7b",
}

def _remap_model(name: str) -> str:
    name = (name or "").strip()
    return _MODEL_REMAP.get(name, name)

def _split_models_csv(s: str) -> List[str]:
    """
    يفصل سلسلة موديلات (comma/newline/semicolon) ويشيل:
    - الفراغات
    - التكرارات (يحافظ على الترتيب)
    - أي بادئة على شكل key=value (نأخذ ما بعد '=')
    """
    seen, out = set(), []
    for part in re.split(r"[,\n;]+", s or ""):
        tok = part.strip()
        if not tok:
            continue
        if "=" in tok:  # يصلّح أخطاء مثل: CHAT_MODEL=llama-3.1-70b
            tok = tok.split("=", 1)[-1].strip()
        if tok and tok not in seen:
            out.append(tok)
            seen.add(tok)
    return out

# =========================
# Singleton State
# =========================

__LLM_CLIENT_SINGLETON: Optional[OpenAI] = None
__LLM_CLIENT_LOCK = threading.Lock()
__MODELS_CACHE: Optional[Tuple[str, str]] = None

# =========================
# Client Builder (single source)
# =========================

def _build_client() -> Optional[OpenAI]:
    """
    يبني عميل OpenAI-compatible.
    يرجّع None لو ما فيه مفتاح — عشان تتعامل الطبقة العليا مع KB-only.
    """
    key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not key:
        _maybe_log_once("NO API KEY (GROQ_API_KEY/OPENAI_API_KEY/OPENROUTER_API_KEY). KB-only mode.")
        return None

    base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENROUTER_BASE_URL") or ""
    is_groq = bool(os.getenv("GROQ_API_KEY")) or base.startswith("https://api.groq.com")
    is_openrouter = bool(os.getenv("OPENROUTER_API_KEY")) or base.startswith("https://openrouter.ai")

    # ضبط base للـ compat providers
    if not base and is_groq:
        base = "https://api.groq.com/openai/v1"
    if not base and is_openrouter:
        base = "https://openrouter.ai/api/v1"

    org = os.getenv("OPENAI_ORG") or None

    # ترويسات OpenRouter
    default_headers: Dict[str, str] = {}
    if is_openrouter:
        ref = os.getenv("OPENROUTER_REFERRER")
        title = os.getenv("OPENROUTER_APP_TITLE")
        if ref:   default_headers["HTTP-Referer"] = ref  # type: ignore
        if title: default_headers["X-Title"] = title     # type: ignore

    kw: Dict[str, Any] = {"api_key": key}
    if base: kw["base_url"] = base
    if org:  kw["organization"] = org
    if default_headers: kw["default_headers"] = default_headers

    if OpenAI is None:
        return None

    try:
        client = OpenAI(**kw)
        provider = "Groq" if is_groq else ("OpenRouter" if is_openrouter else "OpenAI")
        _maybe_log_once(f"INIT OK | base_url={base or 'default'} | org={bool(org)} | provider={provider}")
        return client
    except Exception as e:
        _maybe_log_once(f"INIT FAILED: {e!r} (base_url={base or '(none)'})")
        return None

def make_llm_client() -> Optional[OpenAI]:
    """واجهة متوافقة مع كودك السابق — تبني العميل (لكن فعليًا سنعيد Singleton)."""
    return make_llm_client_singleton()

def make_llm_client_singleton() -> Optional[OpenAI]:
    """يعيد عميل Singleton (يبني مرة واحدة فقط)."""
    global __LLM_CLIENT_SINGLETON, __MODELS_CACHE
    if __LLM_CLIENT_SINGLETON is not None:
        return __LLM_CLIENT_SINGLETON
    with __LLM_CLIENT_LOCK:
        if __LLM_CLIENT_SINGLETON is None:
            __LLM_CLIENT_SINGLETON = _build_client()
            __MODELS_CACHE = pick_models()
            if __LLM_CLIENT_SINGLETON is not None:
                _maybe_log_once("[LLM_CLIENT] INIT OK (singleton)")
                _maybe_log_once(f"[LLM_CLIENT] MODELS -> main={__MODELS_CACHE[0]}, fb={__MODELS_CACHE[1]}")
    return __LLM_CLIENT_SINGLETON

def get_models_cached() -> Tuple[str, str]:
    """يعيد (main_chain, fallback) مع كاش داخلي."""
    global __MODELS_CACHE
    if __MODELS_CACHE is None:
        _ = make_llm_client_singleton()
    # ضمانات
    if not __MODELS_CACHE:
        __MODELS_CACHE = pick_models()
    return __MODELS_CACHE

def get_client_and_models() -> Tuple[Optional[OpenAI], str, str]:
    """راحة: يرجّع (client, main_chain, fallback)."""
    c = make_llm_client_singleton()
    main, fb = get_models_cached()
    return c, main, fb

# =========================
# Model Picking
# =========================

def pick_models() -> Tuple[str, str]:
    """
    يحدد موديلات المحادثة الافتراضية حسب المزود.
    ملاحظة: تقدر تحط أكثر من موديل في CHAT_MODEL مفصولة بفواصل/أسطر/فواصل منقوطة.
    """
    using_groq = bool(
        os.getenv("GROQ_API_KEY")
        or str(os.getenv("OPENAI_BASE_URL", "")).startswith("https://api.groq.com")
    )
    using_openrouter = bool(
        os.getenv("OPENROUTER_API_KEY")
        or str(os.getenv("OPENROUTER_BASE_URL", "")).startswith("https://openrouter.ai")
    )

    if using_groq:
        chain_default = ",".join([
            "llama-3.1-70b",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ])
        fb_default = "llama-3.1-8b-instant"
    elif using_openrouter:
        # أمثلة شائعة في OpenRouter (استخدم ما لديك فعليًا)
        chain_default = ",".join([
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mixtral-8x7b:free",
        ])
        fb_default = "mistralai/mixtral-8x7b:free"
    else:
        chain_default = ",".join(["gpt-4o", "gpt-4o-mini", "gpt-4.1-mini"])
        fb_default = "gpt-4o-mini"

    raw_main = (os.getenv("CHAT_MODEL", chain_default) or "").strip()
    raw_fb   = (os.getenv("CHAT_MODEL_FALLBACK", fb_default) or "").strip()

    # نظّف السلاسل ثم remap لكل عنصر
    chain = [_remap_model(x) for x in _split_models_csv(raw_main)]
    fb = _remap_model((_split_models_csv(raw_fb)[:1] or [fb_default])[0])

    # ضمّن fallback ضمن السلسلة لو مش موجود
    if fb and fb not in chain:
        chain.append(fb)

    main_chain = ",".join(chain) if chain else fb
    _maybe_log_once(f"MODELS -> main={main_chain}, fb={fb}")
    return (main_chain, fb)

# =========================
# Chat (with rotation)
# =========================

def chat_once(
    client: Optional[OpenAI],
    messages: List[Dict[str, str]],
    model: str,
    *,
    temperature: float = 0.5,
    max_tokens: int = 800,
    top_p: float = 0.9,
    presence_penalty: float = 0.15,
    frequency_penalty: float = 0.1,
    timeout_s: float = 20.0,
    retries: int = 2,
    seed: Optional[int] = None,
) -> str:
    """
    مكالمة دردشة واحدة مع دوران تلقائي على سلسلة موديلات (لو تم تمريرها).
    - عند 400/رفض باراميترات: نحاول نفس الموديل بإزالة penalties وضبط top_p=1
    - عند "model not found"/"decommissioned"/404: ننتقل للمرشح التالي
    - عند فشل المصادقة: رسائل واضحة مع روابط مفيدة
    """
    if client is None:
        error_msg = (
            "\n❌ خطأ: لا يوجد عميل LLM - المفتاح غير مضبوط!\n"
            "\n📋 خطوات الحل:\n"
            "1. احصل على مفتاح API مجاني من:\n"
            "   • Groq (مجاني): https://console.groq.com/keys\n"
            "   • أو OpenAI (مدفوع): https://platform.openai.com/api-keys\n"
            "\n2. ضعه في ملف .env:\n"
            "   GROQ_API_KEY=gsk_your_key_here\n"
            "   أو\n"
            "   OPENAI_API_KEY=sk-proj-your_key_here\n"
            "\n3. احفظ الملف وأعد تشغيل التطبيق\n"
            "\n💡 بديل: فعّل وضع KB فقط في .env:\n"
            "   ENABLE_KB_FALLBACK=true\n"
            "\n"
            "ERROR: No LLM client - API key not configured!\n"
            "\nSOLUTIONS:\n"
            "1. Get FREE API key from:\n"
            "   • Groq: https://console.groq.com/keys\n"
            "   • Or OpenAI: https://platform.openai.com/api-keys\n"
            "\n2. Add to .env file:\n"
            "   GROQ_API_KEY=gsk_your_key_here\n"
            "   or\n"
            "   OPENAI_API_KEY=sk-proj-your_key_here\n"
            "\n3. Save and restart app\n"
            "\nALTERNATIVE: Enable KB-only mode in .env:\n"
            "   ENABLE_KB_FALLBACK=true\n"
        )
        raise RuntimeError(error_msg)

    # ابنِ قائمة المرشحين
    candidate_models = [_remap_model(x) for x in _split_models_csv(model)]
    if not candidate_models:
        raise RuntimeError("لم يتم توفير أي موديل صالح في 'model'.")

    if seed is None:
        env_seed = os.getenv("LLM_SEED")
        if env_seed:
            try:
                seed = int(env_seed)
            except Exception:
                seed = None

    last_err: Optional[Exception] = None
    for midx, model_id in enumerate(candidate_models):
        _maybe_log_once(f"trying model[{midx}]: {model_id}")
        for attempt in range(retries + 1):
            try:
                client_t = client.with_options(timeout=timeout_s)
                kwargs: Dict[str, Any] = dict(
                    model=model_id,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    presence_penalty=presence_penalty,
                    frequency_penalty=frequency_penalty,
                    max_tokens=max_tokens,
                )
                if seed is not None:
                    kwargs["seed"] = seed  # قد يُتجاهل لدى بعض المزودين

                # المحاولة الأولى
                try:
                    resp = client_t.chat.completions.create(**kwargs)
                except Exception as inner_e:
                    msg = str(inner_e)
                    low = msg.lower()

                    # رفض باراميترات — جرّب نفس الموديل بدون penalties وبـ top_p=1
                    bad_params = ("400" in msg) and (("bad request" in low) or ("invalid" in low))
                    not_model_issue = not any(k in low for k in [
                        "model_decommissioned", "no such model", "model not found",
                        "unknown model", "does not exist", "404"
                    ])
                    if bad_params and not_model_issue:
                        _maybe_log_once("retrying without penalties/top_p due to provider param rejection…")
                        kwargs.pop("presence_penalty", None)
                        kwargs.pop("frequency_penalty", None)
                        kwargs["top_p"] = 1.0
                        resp = client_t.chat.completions.create(**kwargs)
                    else:
                        raise

                content = (resp.choices[0].message.content if resp and getattr(resp, "choices", None) else "") or ""
                return content.strip()

            except Exception as e:
                last_err = e
                emsg = str(e).lower()
                
                # معالجة خاصة لأخطاء المصادقة
                if any(k in emsg for k in ["authentication", "unauthorized", "invalid api key", "incorrect api key", "401"]):
                    error_msg = (
                        "\n❌ خطأ في المصادقة: مفتاح API غير صحيح أو منتهي الصلاحية!\n"
                        "\n📋 خطوات الحل:\n"
                        "1. تحقق من مفتاح API في ملف .env\n"
                        "2. مفاتيح Groq تبدأ بـ: gsk_\n"
                        "3. مفاتيح OpenAI تبدأ بـ: sk-proj- أو sk-\n"
                        "4. لا توجد مسافات أو علامات تنصيص حول المفتاح\n"
                        "\n🔑 احصل على مفتاح جديد:\n"
                        "   • Groq (مجاني): https://console.groq.com/keys\n"
                        "   • OpenAI (مدفوع): https://platform.openai.com/api-keys\n"
                        "\n"
                        "ERROR: Authentication failed - Invalid or expired API key!\n"
                        "\nSOLUTIONS:\n"
                        "1. Check your API key in .env file\n"
                        "2. Groq keys start with: gsk_\n"
                        "3. OpenAI keys start with: sk-proj- or sk-\n"
                        "4. No spaces or quotes around the key\n"
                        "\nGET NEW KEY:\n"
                        "   • Groq (free): https://console.groq.com/keys\n"
                        "   • OpenAI: https://platform.openai.com/api-keys\n"
                    )
                    _log(error_msg)
                    raise RuntimeError(error_msg) from e
                
                _maybe_log_once(f"chat attempt#{attempt} failed on {model_id}: {e!r}")

                # الموديل متوقف/غير موجود → انتقل للمرشح التالي فورًا
                if any(k in emsg for k in [
                    "model_decommissioned", "no such model", "model not found", "unknown model",
                    "does not exist", "404"
                ]):
                    _maybe_log_once(f"model unavailable: {model_id} → try next candidate")
                    break  # إلى الموديل التالي

                # وإلا → إعادة محاولة لنفس الموديل (exponential backoff)
                if attempt < retries:
                    time.sleep(0.6 * (2 ** attempt) + random.random() * 0.2)
                else:
                    break  # خلصت محاولات هذا الموديل

    raise RuntimeError(f"فشل chat_once بعد تدوير كل الموديلات: {last_err}")

# =========================
# Optional: Streamlit Cache
# =========================

def get_streamlit_client() -> Optional[OpenAI]:
    """
    إن كنت تستخدم Streamlit، هذه الدالة تعيد عميلًا بكاش resource.
    تعمل حتى لو لم تتوفر streamlit (ترجع Singleton عادي).
    """
    try:
        import streamlit as st  # type: ignore

        @st.cache_resource(show_spinner=False)
        def _client_cached():
            return make_llm_client_singleton()

        return _client_cached()
    except Exception:
        # fallback: Singleton العادي
        return make_llm_client_singleton()

# =========================
# __all__
# =========================

__all__ = [
    "make_llm_client",
    "make_llm_client_singleton",
    "pick_models",
    "get_models_cached",
    "chat_once",
    "get_client_and_models",
    "get_streamlit_client",
]
