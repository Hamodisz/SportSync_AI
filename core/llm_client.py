# core/llm_client.py
# -*- coding: utf-8 -*-
"""
موحِّد للاتصال بنماذج OpenAI/Groq (واجهة OpenAI المتوافقة).
- يقرأ المفاتيح من GROQ_API_KEY أو OPENAI_API_KEY أو OPENROUTER_API_KEY أو AZURE_OPENAI_API_KEY
- يضبط base_url تلقائيًا لو كان مفتاح Groq موجود
- يعرّف دوال بسيطة: make_llm_client, pick_models, chat_once
"""

from __future__ import annotations
import os
from typing import List, Dict, Optional

try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("ثبّت الحزمة: openai>=1.6.1,<2") from e


def make_llm_client() -> Optional[OpenAI]:
    key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("AZURE_OPENAI_API_KEY")
    )
    if not key:
        return None

    base = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENROUTER_BASE_URL")
        or os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    # لو في مفتاح Groq وما في base_url، عيّنه تلقائيًا
    if not base and os.getenv("GROQ_API_KEY"):
        base = "https://api.groq.com/openai/v1"

    org = os.getenv("OPENAI_ORG") or None
    kw = {"api_key": key}
    if base:
        kw["base_url"] = base
    if org:
        kw["organization"] = org
    return OpenAI(**kw)


def pick_models() -> Dict[str, str]:
    """
    يختار النموذج الرئيسي والبديل حسب البيئة/الموفر.
    - يدعم override عبر CHAT_MODEL و CHAT_MODEL_FALLBACK
    """
    using_groq = bool(
        os.getenv("GROQ_API_KEY")
        or str(os.getenv("OPENAI_BASE_URL", "")).startswith("https://api.groq.com")
    )
    main_default = "llama3-70b-8192" if using_groq else "gpt-4o"
    fb_default   = "llama3-8b-8192"  if using_groq else "gpt-4o-mini"

    return {
        "main": os.getenv("CHAT_MODEL", main_default),
        "fallback": os.getenv("CHAT_MODEL_FALLBACK", fb_default),
    }


def chat_once(
    client: OpenAI,
    messages: List[Dict[str, str]],
    model: str,
    *,
    temperature: float = 0.5,
    max_tokens: int = 800,
    top_p: float = 0.9,
    presence_penalty: float = 0.15,
    frequency_penalty: float = 0.1,
    timeout_s: float = 20.0,
) -> str:
    """استدعاء واحد بسيط."""
    if client is None:
        raise RuntimeError("لا يوجد عميل LLM (المفتاح غير مضبوط)")

    client_t = client.with_options(timeout=timeout_s)
    resp = client_t.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()
