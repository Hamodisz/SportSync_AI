# -*- coding: utf-8 -*-
import os, sys, json, time, uuid
from pathlib import Path
from typing import List
import streamlit as st

# =========================
# ضبط صفحة ستريملت (مرّة وحدة)
# =========================
if "page_configured" not in st.session_state:
    st.set_page_config(page_title="SportSync — Quiz", page_icon="🎯", layout="centered")
    st.session_state["page_configured"] = True

# =========================
# مسارات مرنة (محلي + Render)
# =========================
try:
    HERE = Path(__file__).resolve().parent
except NameError:
    HERE = Path.cwd()

ROOT = HERE.parent if HERE.name in ("quiz_service",) else HERE
for p in (ROOT, ROOT / "core", ROOT / "analysis"):
    sp = str(p.resolve())
    if sp not in sys.path:
        sys.path.insert(0, sp)

# =========================
# Helpers
# =========================
def _safe_str(x) -> str:
    """يحوّل أي نوع نص/قائمة/ديكت إلى نص قابل للعرض."""
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (list, tuple, set)):
        flat = []
        for item in x:
            if isinstance(item, (list, tuple, set)):
                flat.append(_safe_str(list(item)))
            elif isinstance(item, dict):
                for k in ("text", "desc", "value", "answer", "label", "title"):
                    if k in item and isinstance(item[k], str) and item[k].strip():
                        flat.append(item[k].strip())
                        break
                else:
                    try:
                        flat.append(json.dumps(item, ensure_ascii=False))
                    except Exception:
                        flat.append(str(item))
            else:
                flat.append(str(item))
        return "، ".join([s for s in (str(i).strip() for i in flat) if s])
    if isinstance(x, dict):
        for k in ("text", "desc", "value", "answer", "label", "title"):
            if k in x and isinstance(x[k], str):
                return x[k]
        try:
            return json.dumps(x, ensure_ascii=False)
        except Exception:
            return str(x)
    return str(x)

def _is_followup_cards(recs_list):
    """نحدد هل اللي ظهر هو بطاقة متابعة (Evidence Gate)."""
    if not isinstance(recs_list, (list, tuple)) or not recs_list:
        return False
    head = _safe_str(recs_list[0]).strip().lower()
    return ("🧭" in _safe_str(recs_list[0])) or ("need a few quick answers" in head) or ("نحتاج إجابات" in head) or (len(recs_list) >= 2 and _safe_str(recs_list[1]).strip() == "—")

# =========================
# استيرادات مع بدائل آمنة
# =========================
try:
    from core.backend_gpt import generate_sport_recommendation
except Exception:
    def generate_sport_recommendation(answers, lang="العربية"):
        return [
            "❌ لم يتم تهيئة عميل الـ LLM في خدمة الـ Quiz (تأكد من المتغيرات البيئية والنشر).",
            "—",
            "—",
        ]

try:
    from core.dynamic_chat import start_dynamic_chat
except Exception:
    def start_dynamic_chat(**kwargs):
        user_msg = kwargs.get("user_message", "")
        return f"فهمت: {_safe_str(user_msg)}\nسنعدّل الخطة تدريجيًا ونراعي تفضيلاتك خطوة بخطوة."

try:
    # ستريم حقيقي إن وفّرته لاحقًا
    from core.dynamic_chat import start_dynamic_chat_stream  # generator
except Exception:
    start_dynamic_chat_stream = None

# Layer Z قد تكون في core أو analysis
try:
    from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception:
    try:
        from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
    except Exception:
        def analyze_silent_drivers(answers, lang="العربية"):
            return ["تحفيز قصير المدى", "إنجازات سريعة", "تفضيل تدريبات فردية"]

# (تشخيص) معرفة حالة LLM — باستخدام عميلك الموحّد
try:
    from core.llm_client import get_client_and_models, get_models_cached
    _LLM_CLIENT_FOR_DIAG, _MAIN_CHAIN, _FB_MODEL = get_client_and_models()
except Exception:
    _LLM_CLIENT_FOR_DIAG = None
    _MAIN_CHAIN = os.getenv("CHAT_MODEL", "gpt-4o")
    _FB_MODEL = os.getenv("CHAT_MODEL_FALLBACK", "gpt-4o-mini")

# ✅ User Logger (صامت عند غيابه)
try:
    from core.user_logger import (
        log_quiz_submission, log_rating, log_chat_message, log_event
    )
except Exception:
    def log_quiz_submission(**kw): return kw.get("session_id") or "nosession"
    def log_rating(**kw): pass
    def log_chat_message(**kw): pass
    def log_event(**kw): pass

# =========================
# إعدادات واجهة + لغة
# =========================
lang = st.sidebar.radio("🌐 اختر اللغة / Choose Language", ["العربية", "English"], index=0)
is_ar = (lang == "العربية")
T = (lambda ar, en: ar if is_ar else en)

# ✅ تحكم بالتجربة
with st.sidebar.expander(T("⚙ إعدادات العرض", "⚙ Display Settings"), expanded=True):
    LIVE_TYPING = st.checkbox(T("إظهار كتابة حيّة (typewriter)", "Show live typing (typewriter)"), value=True)
    SHOW_THINKING = st.checkbox(T("إظهار مراحل التفكير", "Show thinking stages"), value=True)
    TYPE_SPEED_MS = st.slider(T("سرعة الكتابة (ملّي ثانية/حرف)", "Typing speed (ms/char)"), 1, 30, value=6)

# 🧪 Diagnostics (اختياري)
with st.sidebar.expander("🧪 Diagnostics", expanded=False):
    st.write("Model chain (main):", _MAIN_CHAIN)
    st.write("Model (fallback):", _FB_MODEL)
    st.write("LLM ready:", bool(_LLM_CLIENT_FOR_DIAG))
    st.write("GROQ key set:", bool(os.getenv("GROQ_API_KEY")))
    st.write("OPENAI key set:", bool(os.getenv("OPENAI_API_KEY")))
    st.write("OPENROUTER key set:", bool(os.getenv("OPENROUTER_API_KEY")))
    st.write(
        "Base URL:",
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENROUTER_BASE_URL")
        or os.getenv("AZURE_OPENAI_ENDPOINT")
        or "default",
    )
    try:
        from core.memory_cache import get_cache_stats, clear_cache
        stats = get_cache_stats()
        st.write("Cache hits:", stats.get("hits"))
        st.write("Cache misses:", stats.get("misses"))
        st.write("Cache size:", stats.get("size"))
        st.write("Last action:", stats.get("last_action"))
        st.write("Last get (ms):", stats.get("last_get_ms"))
        if st.button("🧹 Clear cache"):
            clear_cache()
            st.rerun()
    except Exception:
        pass

# =========================
# تحميل الأسئلة
# =========================
QUESTIONS_DIR = (ROOT / "questions")
if not QUESTIONS_DIR.exists():
    QUESTIONS_DIR = HERE / "questions"

ar_path = QUESTIONS_DIR / "arabic_questions.json"
en_path = QUESTIONS_DIR / "english_questions.json"
q_path = ar_path if is_ar or not en_path.exists() else en_path

if not q_path.exists():
    st.error(T("❌ لم يتم العثور على ملف الأسئلة.", "❌ Questions file not found."))
    st.stop()

with q_path.open("r", encoding="utf-8") as f:
    questions = json.load(f)

# =========================
# Helpers: كتابة حيّة + ستاتس
# =========================
def typewriter_write(container, text: str, ms_per_char: int = 6):
    """كتابة حيّة داخل نفس الوعاء."""
    text = _safe_str(text)
    if not LIVE_TYPING:
        container.markdown(text)
        return
    buf = []
    for ch in text:
        buf.append(ch)
        container.markdown("".join(str(x) for x in buf))
        time.sleep(max(ms_per_char, 1) / 1000.0)

def typewriter_chat(role: str, text: str, ms_per_char: int = 6):
    """عرض رسالة شات بكتابة حيّة."""
    with st.chat_message(role):
        ph = st.empty()
        typewriter_write(ph, text, ms_per_char)

def status_steps(enabled: bool):
    """Context manager بسيط لمراحل التفكير."""
    class _Dummy:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def write(self, *a, **k): pass
        def update(self, *a, **k): pass
        def info(self, *a, **k): pass
        def warning(self, *a, **k): pass
        def success(self, *a, **k): pass

    if not enabled:
        return _Dummy()

    try:
        # Streamlit >= 1.25
        return st.status(T("🤖 يفكّر الآن…", "🤖 Thinking…"), expanded=True)
    except Exception:
        class _Alt:
            def __init__(self):
                self.box = st.empty()
                self.lines = []
                self.box.write("\n".join(_safe_str(x) for x in self.lines))
            def __enter__(self):
                return self
            def __exit__(self, *exc):
                return False
            def write(self, text):
                self.lines.append(_safe_str(text))
                self.box.write("\n".join(_safe_str(x) for x in self.lines))
            def info(self, text): self.write("ℹ " + _safe_str(text))
            def warning(self, text): self.write("⚠ " + _safe_str(text))
            def success(self, text): self.write("✅ " + _safe_str(text))
            def update(self, **kwargs): pass
        return _Alt()

# =========================
# واجهة الأسئلة
# =========================
st.title(T("🎯 توصيتك الرياضية الذكية", "🎯 Your Smart Sport Recommendation"))

answers = {}
for q in questions:
    q_key = q.get("key", f"q_{len(answers)+1}")
    text_ar = q.get("question_ar", "")
    text_en = q.get("question_en", text_ar)
    text = text_ar if is_ar else text_en

    choices = q.get("multiple_choices")
    allow_custom = bool(q.get("allow_custom", False))

    if choices and isinstance(choices, list):
        sel = st.multiselect(text, [str(c) for c in choices], key=q_key)
        if allow_custom:
            custom = st.text_input(T("✏ إجابتك الخاصة (اختياري)", "✏ Your own answer (optional)"),
                                   key=f"{q_key}_custom")
            if custom:
                sel.append(custom)
        answers[q_key] = {"question": _safe_str(text), "answer": sel}
    else:
        t = st.text_input(text, key=q_key)
        answers[q_key] = {"question": _safe_str(text), "answer": _safe_str(t)}

st.divider()

# =========================
# أزرار التحكم
# =========================
c1, c2, c3 = st.columns([1,1,1])
go  = c1.button(T("🔍 اعرض التوصيات", "🔍 Show Recommendations"))
rst = c2.button(T("🔄 إعادة الاختبار", "🔄 Restart"))
dl  = c3.button(T("⬇ تنزيل التوصيات نصيًا", "⬇ Download Recommendations as text"))

if rst:
    st.session_state.clear()
    st.rerun()

# حالة عامة
st.session_state.setdefault("recs", [])
st.session_state.setdefault("ratings", [4, 4, 4])
st.session_state.setdefault("chat_open", False)
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("z_drivers", [])
st.session_state.setdefault("session_id", uuid.uuid4().hex)

# =========================
# توليد التوصيات + Layer Z (مع مراحل تفكير)
# =========================
if go:
    user_id = "web_user"

    # اربط الـsession_id بالإجابات ليسحبها backend_gpt للّوق
    answers["_session_id"] = st.session_state["session_id"]
    # سجّل submission
    try:
        log_quiz_submission(
            user_id=user_id,
            answers=answers,
            lang=lang,
            session_id=st.session_state["session_id"],
            meta={"source": "quiz_ui"}
        )
    except Exception:
        pass

    with status_steps(SHOW_THINKING) as stat:
        try:
            if SHOW_THINKING: stat.info(T("تحليل الإجابات…", "Analyzing answers…"))
            # ➊ توليد التوصيات
            raw_recs = generate_sport_recommendation(answers, lang=lang)
            cleaned = []
            if isinstance(raw_recs, (list, tuple)):
                for r in list(raw_recs)[:3]:
                    cleaned.append(_safe_str(r))
            else:
                cleaned = [_safe_str(raw_recs)]
            st.session_state["recs"] = cleaned[:3]
            # 🔔 افتح المحادثة تلقائيًا إذا كانت Follow-ups
            if _is_followup_cards(st.session_state["recs"]):
                st.session_state["chat_open"] = True
                try:
                    log_event(
                        user_id=user_id,
                        session_id=st.session_state["session_id"],
                        name="open_chat",
                        payload={"reason": "followups_auto"},
                        lang=lang
                    )
                except Exception:
                    pass
            if SHOW_THINKING: stat.info(T("مواءمة مع محاور Z…", "Aligning with Z-axes…"))
        except Exception as e:
            st.error(T("خطأ أثناء توليد التوصيات: ", "Error generating recommendations: ") + _safe_str(e))
            st.session_state["recs"] = []

        # ➋ Layer Z
        try:
            z = analyze_silent_drivers(answers, lang=lang) or []
        except Exception:
            z = []
        st.session_state["z_drivers"] = [ _safe_str(i) for i in (z or []) ]

        if SHOW_THINKING:
            if z:
                stat.info(T("تثبيت البصمة النفسية (Z)…", "Locking psycho-metrics (Z)…"))
            stat.success(T("جاهزة ✅", "Ready ✅"))

# =========================
# عرض Layer Z
# =========================
z = st.session_state.get("z_drivers", [])
if z:
    st.subheader(T("🧭 ما يحركك دون أن تدري", "🧭 Your Silent Drivers"))
    for item in z:
        st.write("• " + _safe_str(item))
    st.divider()

# =========================
# عرض التوصيات (ثلاثة) + التقييم
# =========================
recs = st.session_state.get("recs", [])
if recs:
    headers_ar = ["🟢 التوصية رقم 1", "🌿 التوصية رقم 2", "🔮 التوصية رقم 3 (ابتكارية)"]
    headers_en = ["🟢 Recommendation #1", "🌿 Recommendation #2", "🔮 Recommendation #3 (Creative)"]

    for i, rec_md in enumerate(recs[:3]):
        st.subheader(headers_ar[i] if is_ar else headers_en[i])
        ph = st.empty()
        ph.markdown(_safe_str(rec_md))

        old_val = st.session_state["ratings"][i]
        new_rating = st.slider(
            "⭐ " + T("قيّم هذه التوصية", "Rate this recommendation"),
            1, 5, value=old_val, key=f"rating_{i}"
        )
        if new_rating != old_val:
            st.session_state["ratings"][i] = new_rating
            try:
                log_rating(
                    user_id="web_user",
                    session_id=st.session_state["session_id"],
                    index=i,
                    rating=int(new_rating),
                    lang=lang
                )
            except Exception:
                pass

    st.divider()
    cA, cB = st.columns([1,1])

    open_label = T(
        "🙅‍♂ لم تعجبني — افتح محادثة" if not _is_followup_cards(recs) else "🧭 أكمل الإجابات — افتح محادثة",
        "🙅‍♂ Not satisfied — open chat" if not _is_followup_cards(recs) else "🧭 Complete quick answers — open chat"
    )
    if cA.button(open_label):
        st.session_state["chat_open"] = True
        try:
            log_event(
                user_id="web_user",
                session_id=st.session_state["session_id"],
                name="open_chat",
                payload={"reason": "manual_click", "followups": bool(_is_followup_cards(recs))},
                lang=lang
            )
        except Exception:
            pass

    if dl:
        joined = "\n\n".join(_safe_str(x) for x in recs[:3])
        st.download_button(
            label=T("⬇ تنزيل كملف TXT", "⬇ Download as TXT"),
            data=joined.encode("utf-8"),
            file_name="sportsync_recommendations.txt",
            mime="text/plain"
        )

# =========================
# واجهة محادثة شبيهة بالشات (chat UI)
# =========================
if st.session_state.get("chat_open", False):
    # زر إغلاق سريع
    top_c1, top_c2 = st.columns([1,6])
    if top_c1.button(T("✖ إغلاق المحادثة", "✖ Close Chat")):
        try:
            log_event(
                user_id="web_user",
                session_id=st.session_state["session_id"],
                name="close_chat",
                payload={},
                lang=lang
            )
        except Exception:
            pass
        st.session_state["chat_open"] = False
        st.rerun()

    st.subheader(T("🧠 محادثة المدرب الذكي", "🧠 AI Coach Chat"))

    # عرض السجل القديم
    for msg in st.session_state["chat_history"]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(_safe_str(msg["content"]))

    # تنبيه صغير لو الحالة Follow-ups
    if _is_followup_cards(st.session_state.get("recs", [])):
        st.info(T(
            "🧭 عندنا أسئلة قصيرة جدًا قبل ما نضبط الهوية. اكتب إجابات مختصرة هنا.",
            "🧭 I need a couple of quick answers before I lock the identity. Reply here."
        ))

    user_msg = st.chat_input(
        T("اكتب ما الذي لم يعجبك أو ما الذي تريد تعديله…", "Tell me what you didn’t like or what to adjust…")
    )

    if user_msg:
        # أضف رسالة المستخدم للسجل + لوق
        user_text = _safe_str(user_msg)
        st.session_state["chat_history"].append({"role": "user", "content": user_text})
        try:
            log_chat_message(
                user_id="web_user",
                session_id=st.session_state["session_id"],
                role="user",
                content=user_text,
                lang=lang,
                extra={"where": "quiz_ui"}
            )
        except Exception:
            pass
        typewriter_chat("user", user_text, TYPE_SPEED_MS)

        # حضّر معطيات المكالمة
        recs_for_chat = [ _safe_str(r) for r in st.session_state.get("recs", [])[:3] ]
        ratings = [st.session_state.get(f"rating_{i}", st.session_state["ratings"][i]) for i in range(3)]

        # ردّ المساعد — ستريم حقيقي إن توفر، وإلا كتابة حيّة للناتج النهائي
        if start_dynamic_chat_stream is not None:
            with st.chat_message("assistant"):
                ph = st.empty()
                buf = []
                try:
                    for chunk in start_dynamic_chat_stream(
                        answers=answers,
                        previous_recommendation=recs_for_chat,
                        ratings=ratings,
                        user_id="web_user",
                        lang=lang,
                        chat_history=st.session_state["chat_history"],
                        user_message=user_text
                    ):
                        buf.append(_safe_str(chunk))
                        # عرض فوري لكل chunk - بدون انتظار
                        ph.markdown("".join(_safe_str(x) for x in buf))
                    reply = "".join(_safe_str(x) for x in buf).strip()
                except Exception:
                    reply = T("تم! سنعدّل الخطة بالتدريج حسب ملاحظتك.",
                              "Got it! We’ll adjust the plan gradually based on your feedback.")
                st.session_state["chat_history"].append({"role": "assistant", "content": _safe_str(reply)})
                # لوق ردّ المساعد
                try:
                    log_chat_message(
                        user_id="web_user",
                        session_id=st.session_state["session_id"],
                        role="assistant",
                        content=_safe_str(reply),
                        lang=lang,
                        extra={"where": "quiz_ui"}
                    )
                except Exception:
                    pass
        else:
            try:
                reply = start_dynamic_chat(
                    answers=answers,
                    previous_recommendation=recs_for_chat,
                    ratings=ratings,
                    user_id="web_user",
                    lang=lang,
                    chat_history=st.session_state["chat_history"],
                    user_message=user_text
                )
            except Exception:
                reply = T("تم! سنعدّل الخطة بالتدريج حسب ملاحظتك.",
                          "Got it! We’ll adjust the plan gradually based on your feedback.")
            st.session_state["chat_history"].append({"role": "assistant", "content": _safe_str(reply)})
            # لوق ردّ المساعد
            try:
                log_chat_message(
                    user_id="web_user",
                    session_id=st.session_state["session_id"],
                    role="assistant",
                    content=_safe_str(reply),
                    lang=lang,
                    extra={"where": "quiz_ui"}
                )
            except Exception:
                pass
            typewriter_chat("assistant", _safe_str(reply), TYPE_SPEED_MS)

    st.caption("💬 " + T("تقدر تواصل الدردشة لين توصّل لهويتك الرياضية اللي تحسها ملكك.",
                          "Keep chatting until the plan feels like yours."))

st.caption("🚀 Powered by SportSync AI — Your identity deserves its own sport.")
