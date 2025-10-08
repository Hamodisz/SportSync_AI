# core/llm_client.py
# -*- coding: utf-8 -*-
"""
موحِّد الاتصال بنماذج OpenAI/Groq/OpenRouter/Azure (واجهة OpenAI المتوافقة).
- يقرأ المفاتيح من: GROQ_API_KEY / OPENAI_API_KEY / OPENROUTER_API_KEY / AZURE_OPENAI_API_KEY
- يضبط base_url تلقائيًا (Groq/OpenRouter/Azure)
- يوفّر: make_llm_client, pick_models, chat_once
"""

from __future__ import annotations
import os, time, random
from typing import List, Dict, Optional, Any

try:
    from openai import OpenAI
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
    يدعم Azure بأن يضيف api-version وheader api-key بدل Authorization Bearer.
    """
    key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("AZURE_OPENAI_API_KEY")
    )
    if not key:
        return None

    # اكتشاف الأنماط
    is_groq = bool(os.getenv("GROQ_API_KEY")) or str(os.getenv("OPENAI_BASE_URL", "")).startswith("https://api.groq.com")
    is_openrouter = bool(os.getenv("OPENROUTER_API_KEY")) or str(os.getenv("OPENROUTER_BASE_URL", "")).startswith("https://openrouter.ai")
    is_azure = bool(os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_ENDPOINT"))

    base = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENROUTER_BASE_URL")
        or os.getenv("AZURE_OPENAI_ENDPOINT")  # قد يكون None لغير Azure
    )

    # قواعد base_url الافتراضية
    if not base and is_groq:
        base = "https://api.groq.com/openai/v1"
    if not base and is_openrouter:
        base = "https://openrouter.ai/api/v1"
    # Azure: لازم يكون endpoint مثل: https://<name>.openai.azure.com
    # ونستخدم المسار /openai/deployments ونمرر api-version كـ default_query
    azure_version = os.getenv("OPENAI_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION") or "2024-02-01"
    if is_azure:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or base
        if not endpoint:
            return None
        base = endpoint.rstrip("/") + "/openai/deployments"

    org = os.getenv("OPENAI_ORG") or None

    # إعدادات العميل
    kw: Dict[str, Any] = {}
    default_headers: Dict[str, str] = {}
    default_query: Dict[str, str] = {}

    if is_azure:
        # Azure يستخدم header: api-key ولا يستعمل Bearer
        kw["api_key"] = None
        default_headers["api-key"] = key
        default_query["api-version"] = azure_version
    else:
        kw["api_key"] = key

    if base:
        kw["base_url"] = base
    if org:
        kw["organization"] = org

    # OpenRouter headers الاختيارية (تحسّن الـrate/نسبة القبول)
    if is_openrouter:
        ref = os.getenv("OPENROUTER_REFERRER")
        title = os.getenv("OPENROUTER_APP_TITLE")
        if ref:
            default_headers["HTTP-Referer"] = ref
        if title:
            default_headers["X-Title"] = title

    if default_headers:
        kw["default_headers"] = default_headers
    if default_query:
        kw["default_query"] = default_query

    try:
        return OpenAI(**kw)
    except Exception:
        # لو فشل البناء لأي سبب، رجّع None حتى يكمّل النظام بدون LLM
        return None


def pick_models() -> Dict[str, str]:
    """
    يختار النموذج الرئيسي والبديل حسب المزود. يمكن override عبر CHAT_MODEL و CHAT_MODEL_FALLBACK.
    - Groq: llama3
    - Azure/OpenAI: gpt-4o / gpt-4o-mini (أو Deployment names مع Azure)
    - OpenRouter: gpt-4o كافتراضي (يمكن تغييره)
    """
    using_groq = bool(
        os.getenv("GROQ_API_KEY")
        or str(os.getenv("OPENAI_BASE_URL", "")).startswith("https://api.groq.com")
    )
    using_azure = bool(os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_ENDPOINT"))
    using_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))

    if using_groq:
        main_default = "llama3-70b-8192"
        fb_default = "llama3-8b-8192"
    else:
        # سواء OpenAI أو OpenRouter أو Azure (يفترض أن يكون اسم الـdeployment في Azure)
        main_default = "gpt-4o"
        fb_default = "gpt-4o-mini"

    # في Azure، الاسم هنا يجب أن يطابق "deployment name" وليس اسم الموديل الأصلي
    main = os.getenv("CHAT_MODEL", main_default)
    fb = os.getenv("CHAT_MODEL_FALLBACK", fb_default)

    # تلميح: لو Azure وما عرّفت deployment، ستفشل المكالمة. لذلك نوّضح باللوج إن رغبت.
    return {"main": main, "fallback": fb}


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
) -> str:
    """
    استدعاء واحد بسيط مع retries/backoff.
    - يمرّر seed لو LLM_SEED موجود (بعض المزودين يدعمه).
    """
    if client is None:
        raise RuntimeError("لا يوجد عميل LLM (المفتاح غير مضبوط أو فشل التهيئة)")

    last_err: Optional[Exception] = None
    seed_env = os.getenv("LLM_SEED")
    seed_val: Optional[int] = None
    if seed_env:
        try:
            seed_val = int(seed_env)
        except Exception:
            seed_val = None

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
            if seed_val is not None:
                # ليس كل مزود يدعمه؛ لو تجاهله المزود ما يضر
                create_kwargs["seed"] = seed_val

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
