# -*- coding: utf-8 -*-
"""
موحِّد الاتصال بنماذج OpenAI/Groq/OpenRouter (واجهة OpenAI المتوافقة).
- يقرأ المفاتيح من env ثم .env ثم st.secrets (إن وُجدت)
- يضبط base_url تلقائيًا (Groq/OpenRouter) إذا لم يُمرَّر OPENAI_BASE_URL
- يوفّر: make_llm_client, pick_models, chat_once
- يدعم سلسلة موديلات (comma-separated) مع دوران تلقائي + remap للأسماء القديمة.
"""

from __future__ import annotations
import os, time, random, re
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

# =========================
# Utilities
# =========================
def _log(msg: str) -> None:
    print(f"[LLM_CLIENT] {msg}")

def _bootstrap_env() -> None:
    """حمّل المفاتيح من .env و st.secrets بدون ما تكسّر أي قيم موجودة في env."""
    # 1) .env (محلي/كودسبيس/Render)
    try:
        from dotenv import load_dotenv  # type: ignore
        ROOT = Path(__file__).resolve().parent.parent
        for env_path in (ROOT / ".env", Path.cwd() / ".env"):
            if env_path.exists():
                load_dotenv(env_path, override=False)
                _log(f"dotenv loaded: {env_path}")
                break
    except Exception:
        pass

    # 2) st.secrets (Streamlit) — لا نكتب فوق env إن كان موجود
    try:
        # تجنّب رسالة "No secrets files found" ليس ضروريًا، لكنها غير مؤذية
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
        ):
            _pull(k)
        if secrets:
            _log("streamlit secrets merged into env (non-overriding).")
    except Exception:
        pass

_bootstrap_env()

# =========================
# OpenAI-compatible client
# =========================
try:
    from openai import OpenAI  # openai >= 1.6,<2
except Exception as e:
    raise RuntimeError("ثبّت الحزمة: openai>=1.6.1,<2") from e

# --- خرائط النماذج (حلّ تلقائي لإيقافات/أسماء قديمة) ---
_MODEL_REMAP: Dict[str, str] = {
    # Groq: إيقافات قديمة -> بدائل جديدة
    "llama3-70b-8192": "llama-3.1-70b-versatile",
    "llama3-8b-8192":  "llama-3.1-8b-instant",
    "llama3-70b":      "llama-3.1-70b-versatile",
    "llama3-8b":       "llama-3.1-8b-instant",
}

def _remap_model(name: str) -> str:
    return _MODEL_REMAP.get(name, name)

def _split_models_csv(s: str) -> List[str]:
    """يفصل سلسلة موديلات مفصولة بفواصل، ويشيل الفراغات والتكرار ويحافظ على الترتيب."""
    seen, out = set(), []
    for part in re.split(r"[,\n]+", s or ""):
        mid = part.strip()
        if mid and mid not in seen:
            out.append(mid)
            seen.add(mid)
    return out

def make_llm_client() -> Optional[OpenAI]:
    """
    يبني عميل OpenAI-compatible.
    يرجّع None لو ما فيه مفتاح — عشان يكمل النظام بالـKB فقط.
    """
    key_src = "NONE"
    key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not key:
        _log("NO API KEY found (tried GROQ_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY). Running in KB-only mode.")
        return None

    base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENROUTER_BASE_URL") or ""
    is_groq = bool(os.getenv("GROQ_API_KEY")) or base.startswith("https://api.groq.com")
    is_openrouter = bool(os.getenv("OPENROUTER_API_KEY")) or base.startswith("https://openrouter.ai")

    # ضبط base للـcompat providers
    if not base and is_groq:
        base = "https://api.groq.com/openai/v1"
    if not base and is_openrouter:
        base = "https://openrouter.ai/api/v1"

    org = os.getenv("OPENAI_ORG") or None

    # ترويسات OpenRouter
    default_headers: Dict[str, str] = {}
    if is_openrouter:
        if os.getenv("OPENROUTER_REFERRER"):
            default_headers["HTTP-Referer"] = os.getenv("OPENROUTER_REFERRER")  # type: ignore
        if os.getenv("OPENROUTER_APP_TITLE"):
            default_headers["X-Title"] = os.getenv("OPENROUTER_APP_TITLE")  # type: ignore

    kw: Dict[str, Any] = {"api_key": key}
    if base: kw["base_url"] = base
    if org:  kw["organization"] = org
    if default_headers: kw["default_headers"] = default_headers

    try:
        client = OpenAI(**kw)
        provider = "Groq" if is_groq else ("OpenRouter" if is_openrouter else "OpenAI")
        _log(f"INIT OK | base_url={base or 'default'} | org={bool(org)} | provider={provider}")
        return client
    except Exception as e:
        _log(f"INIT FAILED: {e!r}")
        _log(f"   -> base_url: {base or '(none)'}")
        return None

def pick_models() -> Tuple[str, str]:
    """
    يحدد موديلات المحادثة الافتراضية حسب المزود.
    ملاحظة: تقدر تحط أكثر من موديل في CHAT_MODEL مفصولة بفواصل.
    """
    using_groq = bool(
        os.getenv("GROQ_API_KEY")
        or str(os.getenv("OPENAI_BASE_URL", "")).startswith("https://api.groq.com")
    )
    if using_groq:
        chain_default = ",".join([
            "llama-3.2-90b-text-preview",   # قد تُوقف لاحقاً
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ])
        main_default = chain_default
        fb_default   = "llama-3.1-8b-instant"
    else:
        main_default = "gpt-4o,gpt-4o-mini,gpt-4.1-mini"
        fb_default   = "gpt-4o-mini"

    main = os.getenv("CHAT_MODEL", main_default).strip()
    fb   = os.getenv("CHAT_MODEL_FALLBACK", fb_default).strip()

    # remap لكل عنصر في السلسلة
    chain = [_remap_model(x) for x in _split_models_csv(main)]
    if fb:
        fb = _remap_model(fb)
        if fb not in chain:
            chain.append(fb)
    main_chain = ",".join(chain)

    _log(f"MODELS -> main={main_chain}, fb={fb}")
    return (main_chain, fb)

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
    مكالمة دردشة واحدة مع دوران تلقائي على سلسلة موديلات (لو تم تمريرها بفواصل).
    - عند 400 model_decommissioned/invalid/404 → نجرب الموديل التالي مباشرةً.
    - عند 400 رفض باراميترات (top_p/penalties) نحذفها ثم نعيد المحاولة لنفس الموديل.
    """
    if client is None:
        raise RuntimeError("لا يوجد عميل LLM (المفتاح غير مضبوط أو فشل التهيئة)")

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
        _log(f"trying model[{midx}]: {model_id}")
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
                    kwargs["seed"] = seed  # قد يُتجاهل عند بعض المزودين

                try:
                    resp = client_t.chat.completions.create(**kwargs)
                except Exception as inner_e:
                    msg = str(inner_e)
                    # رفض باراميترات — جرّب نفس الموديل بدون penalties وبـ top_p=1
                    if ("400" in msg) and (("bad request" in msg.lower()) or ("invalid" in msg.lower())) and not any(
                        k in msg.lower() for k in ["model_decommissioned", "no such model", "model not found"]
                    ):
                        _log("retrying without penalties/top_p due to provider param rejection…")
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
                _log(f"chat attempt#{attempt} failed on {model_id}: {e!r}")

                # إذا الموديل متوقف/غير موجود → اطلع من حلقة المحاولات وجرب اللي بعده
                if any(k in emsg for k in ["model_decommissioned", "no such model", "model not found", "unknown model", "does not exist", "404"]):
                    _log(f"model looks unavailable: {model_id} → trying next candidate (if any)…")
                    break  # انتقل للموديل التالي مباشرةً

                # وإلا → إعادة محاولة لنفس الموديل (exponential backoff)
                if attempt < retries:
                    time.sleep(0.6 * (2 ** attempt) + random.random() * 0.2)
                else:
                    break  # خلصت محاولات هذا الموديل

    raise RuntimeError(f"فشل chat_once بعد تدوير كل الموديلات: {last_err}")
