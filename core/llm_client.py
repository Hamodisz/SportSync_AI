# -*- coding: utf-8 -*-
"""
موحِّد الاتصال بنماذج OpenAI/Groq/OpenRouter (واجهة OpenAI المتوافقة).
- يقرأ المفاتيح من env ثم .env ثم st.secrets (إن وُجدت)
- يضبط base_url تلقائيًا (Groq/OpenRouter) إذا لم يُمرَّر OPENAI_BASE_URL
- يوفّر: make_llm_client, pick_models, chat_once
"""

from __future__ import annotations
import os, time, random
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

# =========================
# Bootstrap للبيئة (env / .env / st.secrets)
# =========================
def _log(msg: str) -> None:
    print(f"[LLM_CLIENT] {msg}")

def _bootstrap_env() -> None:
    """حمّل المفاتيح من .env و st.secrets بدون ما تكسّر أي قيم موجودة في env."""
    # 1) .env (محلي/كودسبيس)
    try:
        from dotenv import load_dotenv  # type: ignore
        ROOT = Path(__file__).resolve().parent.parent
        # جرّب .env في الجذر ثم في cwd
        for env_path in (ROOT / ".env", Path.cwd() / ".env"):
            if env_path.exists():
                load_dotenv(env_path, override=False)
                _log(f"dotenv loaded: {env_path}")
                break
    except Exception:
        pass

    # 2) st.secrets (ستريmlit) — لا نكتب فوق env إن كان موجود
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


def make_llm_client() -> Optional[OpenAI]:
    """
    يبني عميل OpenAI-compatible.
    يرجّع None لو ما فيه مفتاح — عشان يكمل النظام بالـKB فقط.
    يطبع سبب الفشل في اللوج بدل الصمت.
    """
    key_src = "NONE"
    key = os.getenv("GROQ_API_KEY")
    if key:
        key_src = "GROQ_API_KEY"
    else:
        key = os.getenv("OPENAI_API_KEY")
        if key:
            key_src = "OPENAI_API_KEY"
        else:
            key = os.getenv("OPENROUTER_API_KEY")
            if key:
                key_src = "OPENROUTER_API_KEY"

    if not key:
        _log("NO API KEY found (tried GROQ_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY). Running in KB-only mode.")
        return None

    base = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENROUTER_BASE_URL")
        or ""
    )

    is_groq = bool(os.getenv("GROQ_API_KEY")) or base.startswith("https://api.groq.com")
    is_openrouter = bool(os.getenv("OPENROUTER_API_KEY")) or base.startswith("https://openrouter.ai")

    # تنبيه لو أكثر من مفتاح
    if sum([
        bool(os.getenv("GROQ_API_KEY")),
        bool(os.getenv("OPENAI_API_KEY")),
        bool(os.getenv("OPENROUTER_API_KEY")),
    ]) > 1:
        _log("WARN: Multiple API keys detected; priority is GROQ > OPENAI > OPENROUTER.")

    # ضبط base للـcompat providers
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
        if ref:   default_headers["HTTP-Referer"] = ref
        if title: default_headers["X-Title"] = title

    kw: Dict[str, Any] = {"api_key": key}
    if base:
        kw["base_url"] = base
    if org:
        kw["organization"] = org
    if default_headers:
        kw["default_headers"] = default_headers

    try:
        client = OpenAI(**kw)
        provider = "Groq" if is_groq else ("OpenRouter" if is_openrouter else "OpenAI")
        _log(f"INIT OK | base_url={base or 'default'} | org={bool(org)} | provider={provider} | key_src={key_src}")
        return client
    except Exception as e:
        _log(f"INIT FAILED: {e!r}")
        _log(f"   -> key_src: {key_src}")
        _log(f"   -> base_url: {base or '(none)'}")
        return None


def pick_models() -> Tuple[str, str]:
    """
    يحدد موديلات المحادثة الافتراضية حسب المزود.
    يمكن override عبر CHAT_MODEL / CHAT_MODEL_FALLBACK.
    """
    using_groq = bool(
        os.getenv("GROQ_API_KEY")
        or str(os.getenv("OPENAI_BASE_URL", "")).startswith("https://api.groq.com")
    )
    if using_groq:
        main_default = "llama3-70b-8192"
        fb_default   = "llama3-8b-8192"
    else:
        main_default = "gpt-4o"
        fb_default   = "gpt-4o-mini"

    main = os.getenv("CHAT_MODEL", main_default)
    fb   = os.getenv("CHAT_MODEL_FALLBACK", fb_default)
    _log(f"MODELS -> main={main}, fb={fb}")
    return (main, fb)


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
    مكالمة دردشة واحدة.
    - يعيد المحاولة تلقائيًا لو حصل خطأ مؤقت.
    - يحاول إزالة بعض الباراميترات إذا رفضها مزوّد الـcompat (400 Bad Request).
    """
    if client is None:
        raise RuntimeError("لا يوجد عميل LLM (المفتاح غير مضبوط أو فشل التهيئة)")

    if seed is None:
        env_seed = os.getenv("LLM_SEED")
        if env_seed:
            try:
                seed = int(env_seed)
            except Exception:
                seed = None

    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            client_t = client.with_options(timeout=timeout_s)
            kwargs: Dict[str, Any] = dict(
                model=model,
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
                # أحيانًا مزوّدات الـcompat ترفض penalties/top_p
                msg = str(inner_e)
                if ("400" in msg) or ("bad request" in msg.lower()) or ("invalid" in msg.lower()):
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
            _log(f"chat attempt#{attempt} failed: {e!r}")
            if attempt >= retries:
                break
            time.sleep(0.6 * (2 ** attempt) + random.random() * 0.2)

    raise RuntimeError(f"فشل chat_once بعد محاولات متعددة: {last_err}")
