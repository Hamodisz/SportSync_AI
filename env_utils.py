# -- coding: utf-8 --
import os
from typing import Optional, Tuple

ENV_KEYS = (
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "AZURE_OPENAI_API_KEY",
)

def get_llm_env() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    يرجّع (api_key, base_url, organization).
    - على Render: خلك على Environment Variables.
    - محليًا: تقدر تستخدم .env (اختياري) بدون رفعه على GitHub.
    """
    api_key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("AZURE_OPENAI_API_KEY")
    )
    base_url = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENROUTER_BASE_URL")
        or os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    # إذا المستخدم حاط GROQ بس ما عرّف base_url — نضبطه تلقائيًا
    if (not base_url) and os.getenv("GROQ_API_KEY"):
        base_url = "https://api.groq.com/openai/v1"

    org = os.getenv("OPENAI_ORG")  # اختياري
    return api_key, base_url, org

def assert_llm_ready() -> None:
    api_key, _, _ = get_llm_env()
    if not api_key:
        raise RuntimeError(
            "مفقود مفتاح LLM: رجاءً ضِف أحد المفاتيح في Render (OPENAI_API_KEY أو GROQ_API_KEY أو OPENROUTER_API_KEY أو AZURE_OPENAI_API_KEY)."
        )

def redacted_env_summary() -> str:
    api_key, base_url, _ = get_llm_env()
    which = "NONE"
    if os.getenv("GROQ_API_KEY"): which = "GROQ_API_KEY"
    elif os.getenv("OPENAI_API_KEY"): which = "OPENAI_API_KEY"
    elif os.getenv("OPENROUTER_API_KEY"): which = "OPENROUTER_API_KEY"
    elif os.getenv("AZURE_OPENAI_API_KEY"): which = "AZURE_OPENAI_API_KEY"

    base = base_url or "default"
    # ما نطبع أي جزء من المفتاح
    return f"LLM READY? {'YES' if api_key else 'NO'} | base={base} | key={which}"
