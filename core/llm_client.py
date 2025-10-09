# core/llm_client.py
# -*- coding: utf-8 -*-
"""
موحِّد الاتصال بنماذج OpenAI/Groq/OpenRouter (واجهة OpenAI المتوافقة).
- يقرأ المفاتيح من: GROQ_API_KEY / OPENAI_API_KEY / OPENROUTER_API_KEY
- يضبط base_url تلقائيًا (Groq/OpenRouter) إذا لم يُمرَّر OPENAI_BASE_URL
- يوفّر: make_llm_client, pick_models, chat_once
- متوافق مع:
    CHAT_MODEL, CHAT_MODEL_FALLBACK = pick_models()
    txt = chat_once(client, messages, CHAT_MODEL, ...)
"""

from __future__ import annotations
import os, time, random
from typing import List, Dict, Optional, Any, Tuple

try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("ثبّت الحزمة: openai>=1.6.1,<2") from e


def make_llm_client() -> Optional[OpenAI]:
    """
    يبني عميل OpenAI-compatible.
    يرجّع None لو ما فيه مفتاح — عشان يكمل النظام بالـKB فقط.
    """
    key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    )
    if not key:
        return None

    # اكتشاف المزود لتهيئة base_url تلقائيًا عند الحاجة
    base = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENROUTER_BASE_URL")
        or ""
    )
    is_groq = bool(os.getenv("GROQ_API_KEY")) or base.startswith("https://api.groq.com")
    is_openrouter = bool(os.getenv("OPENROUTER_API_KEY")) or base.startswith("https://openrouter.ai")

    if not base and is_groq:
        base = "https://api.groq.com/openai/v1"
    if not base and is_openrouter:
        base = "https://openrouter.ai/api/v1"

    org = os.getenv("OPENAI_ORG") or None

    # ترويسات اختيارية لـ OpenRouter
    default_headers: Dict[str, str] = {}
    if is_openrouter:
        ref = os.getenv("OPENROUTER_REFERRER")
        title = os.getenv("OPENROUTER_APP_TITLE")
        if ref:
            default_headers["HTTP-Referer"] = ref
        if title:
            default_headers["X-Title"] = title

    kw: Dict[str, Any] = {"api_key": key}
    if base:
        kw["base_url"] = base
    if org:
        kw["organization"] = org
    if default_headers:
        kw["default_headers"] = default_headers

    try:
        return OpenAI(**kw)
    except Exception:
        # لو فشلت التهيئة لأي سبب، رجّع None (النظام يكمل بدون LLM)
        return None


def pick_models() -> Tuple[str, str]:
    """
    يختار النموذج الرئيسي والبديل حسب المزود. يمكن override عبر CHAT_MODEL و CHAT_MODEL_FALLBACK.
    يرجّع (main, fallback).
    """
    using_groq = bool(
        os.getenv("GROQ_API_KEY")
        or str(os.getenv("OPENAI_BASE_URL", "")).startswith("https://api.groq.com")
    )

    if using_groq:
        main_default = "llama3-70b-8192"
        fb_default = "llama3-8b-8192"
    else:
        main_default = "gpt-4o"
        fb_default = "gpt-4o-mini"

    main = os.getenv("CHAT_MODEL", main_default)
    fb = os.getenv("CHAT_MODEL_FALLBACK", fb_default)
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
    استدعاء واحد بسيط مع retries/backoff.
    - يدعم seed اختياريًا (إذا تجاهله المزود لا يضر).
    - يُرجع نص محتوى أول اختيار.
    """
    if client is None:
        raise RuntimeError("لا يوجد عميل LLM (المفتاح غير مضبوط أو فشل التهيئة)")

    # لو ما مرّرت seed يدويًا، خذه من LLM_SEED إن وُجد
    if seed is None:
        seed_env = os.getenv("LLM_SEED")
        if seed_env:
            try:
                seed = int(seed_env)
            except Exception:
                seed = None

    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            client_t = client.with_options(timeout=timeout_s)
            create_kwargs: Dict[str, Any] = dict(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                max_tokens=max_tokens,
            )
            if seed is not None:
                create_kwargs["seed"] = seed  # قد يُتجاهل من بعض المزودين

            resp = client_t.chat.completions.create(**create_kwargs)
            content = (resp.choices[0].message.content if resp and resp.choices else "") or ""
            return content.strip()
        except Exception as e:
            last_err = e
            if attempt >= retries:
                break
            # backoff + jitter
            time.sleep(0.6 * (2 ** attempt) + random.random() * 0.2)

    raise RuntimeError(f"فشل chat_once بعد محاولات متعددة: {last_err}")
