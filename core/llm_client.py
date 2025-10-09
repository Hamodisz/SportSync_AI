# core/llm_client.py
# -*- coding: utf-8 -*-
"""
موحِّد الاتصال بنماذج OpenAI/Groq/OpenRouter/Azure (واجهة OpenAI المتوافقة).
- يقرأ المفاتيح من: GROQ_API_KEY / OPENAI_API_KEY / OPENROUTER_API_KEY / AZURE_OPENAI_API_KEY
- يضبط base_url تلقائيًا (Groq/OpenRouter)، ويدعم Azure عبر AzureOpenAI
- يوفّر: make_llm_client, pick_models, chat_once
"""

from __future__ import annotations
import os, time, random
from typing import List, Dict, Optional, Any, Tuple

try:
    from openai import OpenAI
    try:
        # متى توفّر AzureOpenAI نستخدمه (SDK >= 1.6)
        from openai import AzureOpenAI  # type: ignore
        _HAS_AZURE = True
    except Exception:
        AzureOpenAI = None  # type: ignore
        _HAS_AZURE = False
except Exception as e:
    raise RuntimeError("ثبّت الحزمة: openai>=1.6.1,<2") from e


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def make_llm_client() -> Optional[OpenAI]:
    """
    يبني عميل OpenAI-compatible. يرجع None لو ما فيه مفتاح — حتى يكمل النظام بالـKB فقط.
    يدعم Azure عبر AzureOpenAI لتولّي المسارات والمعلمات تلقائيًا.
    """
    key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("AZURE_OPENAI_API_KEY")
    )
    if not key:
        return None

    is_groq = bool(os.getenv("GROQ_API_KEY")) or str(os.getenv("OPENAI_BASE_URL", "")).startswith("https://api.groq.com")
    is_openrouter = bool(os.getenv("OPENROUTER_API_KEY")) or str(os.getenv("OPENROUTER_BASE_URL", "")).startswith("https://openrouter.ai")
    is_azure = bool(os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_ENDPOINT"))

    base = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENROUTER_BASE_URL")
        or os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    # Azure: استخدم AzureOpenAI إن توفّر
    if is_azure and _HAS_AZURE:
        azure_version = os.getenv("OPENAI_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION") or "2024-02-01"
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or base
        if not endpoint:
            return None
        try:
            return AzureOpenAI(  # type: ignore
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=azure_version,
                azure_endpoint=endpoint,
            )
        except Exception:
            # لو فشلت تهيئة Azure لأي سبب، نرجّع None ليكمل النظام بدون LLM
            return None

    # غير Azure: OpenAI-compatible (OpenAI/Groq/OpenRouter)
    if not base and is_groq:
        base = "https://api.groq.com/openai/v1"
    if not base and is_openrouter:
        base = "https://openrouter.ai/api/v1"

    org = os.getenv("OPENAI_ORG") or None

    kw: Dict[str, Any] = {}
    default_headers: Dict[str, str] = {}
    default_query: Dict[str, str] = {}

    # OpenRouter: ترويسات اختيارية
    if is_openrouter:
        ref = os.getenv("OPENROUTER_REFERRER")
        title = os.getenv("OPENROUTER_APP_TITLE")
        if ref:
            default_headers["HTTP-Referer"] = ref
        if title:
            default_headers["X-Title"] = title

    kw["api_key"] = key
    if base:
        kw["base_url"] = base
    if org:
        kw["organization"] = org
    if default_headers:
        kw["default_headers"] = default_headers
    if default_query:
        kw["default_query"] = default_query

    try:
        return OpenAI(**kw)
    except Exception:
        return None


def pick_models() -> Tuple[str, str]:
    """
    يختار النموذج الرئيسي والبديل حسب المزود. يمكن override عبر CHAT_MODEL و CHAT_MODEL_FALLBACK.
    * يَرْجِع (main, fallback) ليتوافق مع backend_gpt.py
    """
    using_groq = bool(
        os.getenv("GROQ_API_KEY")
        or str(os.getenv("OPENAI_BASE_URL", "")).startswith("https://api.groq.com")
    )
    using_azure = bool(os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_ENDPOINT"))

    if using_groq:
        main_default = "llama3-70b-8192"
        fb_default = "llama3-8b-8192"
    else:
        # OpenAI/OpenRouter/Azure (في Azure يجب أن يكون اسم الـdeployment)
        main_default = "gpt-4o"
        fb_default = "gpt-4o-mini"

    main = os.getenv("CHAT_MODEL", main_default)
    fb = os.getenv("CHAT_MODEL_FALLBACK", fb_default)

    # تنبيه اختياري يمكن تفعيله بالـLOGS: في Azure يجب أن يكون main/fb اسم deployment فعلي.
    _ = using_azure  # فقط لتهدئة linters
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
    - يعيد string (محتوى أول اختيار).
    """
    if client is None:
        raise RuntimeError("لا يوجد عميل LLM (المفتاح غير مضبوط أو فشل التهيئة)")

    last_err: Optional[Exception] = None

    # لو ما مرّرت seed يدويًا، خذه من LLM_SEED إن وُجد
    if seed is None:
        seed_env = os.getenv("LLM_SEED")
        if seed_env:
            try:
                seed = int(seed_env)
            except Exception:
                seed = None

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
                # ليس كل مزود يدعمه؛ لو تجاهله المزود ما يضر
                create_kwargs["seed"] = seed

            resp = client_t.chat.completions.create(**create_kwargs)
            choice = (resp.choices[0].message.content if resp and resp.choices else "") or ""
            return choice.strip()
        except Exception as e:
            last_err = e
            if attempt >= retries:
                break
            # backoff مع jitter خفيف
            sleep_s = 0.6 * (2 ** attempt) + random.random() * 0.2
            time.sleep(sleep_s)

    raise RuntimeError(f"فشل chat_once بعد محاولات متعددة: {last_err}")
