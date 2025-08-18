# -- coding: utf-8 --
import os, sys, json
from pathlib import Path
import streamlit as st

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
# استيرادات مع بدائل آمنة
# =========================
try:
    from core.backend_gpt import generate_sport_recommendation
except Exception:
    def generate_sport_recommendation(answers, lang="العربية"):
        return [
            "❌ OPENAI_API_KEY غير مضبوط في خدمة الـ Quiz.",
            "—",
            "—",
        ]

try:
    from core.dynamic_chat import start_dynamic_chat
except Exception:
    def start_dynamic_chat(**kwargs):
        user_msg = kwargs.get("user_message", "")
        return f"فهمت: {user_msg}\nسنعدّل الخطة تدريجيًا ونراعي تفضيلاتك خطوة بخطوة."

# Layer Z قد تكون في core أو analysis
try:
    from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception:
    try:
        from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
    except Exception:
        def analyze_silent_drivers(answers, lang="العربية"):
            return ["تحفيز قصير المدى", "إنجازات سريعة", "تفضيل تدريبات فردية"]

# =========================
# تهيئة الصفحة + لغة
# =========================
st.set_page_config(page_title="SportSync — Quiz", page_icon="🎯", layout="centered")
lang = st.sidebar.radio("🌐 اختر اللغة / Choose Language", ["العربية", "English"], index=0)
is_ar = (lang == "العربية")
T = (lambda ar, en: ar if is_ar else en)

# 🧪 Diagnostics (اختياري يظهر في الشريط الجانبي)
try:
    from core.memory_cache import get_cache_stats, clear_cache
    with st.sidebar.expander("🧪 Diagnostics"):
        stats = get_cache_stats()
        st.write("Model:", os.getenv("CHAT_MODEL", "gpt-4o"))
        st.write("OPENAI key set:", bool(os.getenv("OPENAI_API_KEY")))
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
# تحميل الأسئلة (متوافق مع multiple_choices + allow_custom)
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
# واجهة الأسئلة
# =========================
st.title(T("🎯 توصيتك الرياضية الذكية", "🎯 Your Smart Sport Recommendation"))

answers = {}
for q in questions:
    q_key = q.get("key", f"q_{len(answers)+1}")
    text_ar = q.get("question_ar", "")
    text_en = q.get("question_en", text_ar)  # لو ما فيه إنجليزي نعرض العربي
    text = text_ar if is_ar else text_en

    choices = q.get("multiple_choices")
    allow_custom = bool(q.get("allow_custom", False))

    if choices and isinstance(choices, list):
        sel = st.multiselect(text, choices, key=q_key)
        if allow_custom:
            custom = st.text_input(T("✏ إجابتك الخاصة (اختياري)", "✏ Your own answer (optional)"),
                                   key=f"{q_key}_custom")
            if custom:
                sel.append(custom)
        answers[q_key] = {"question": text, "answer": sel}
    else:
        t = st.text_input(text, key=q_key)
        answers[q_key] = {"question": text, "answer": t}

st.divider()

# =========================
# أزرار التحكم
# =========================
col1, col2 = st.columns([1, 1])
go  = col1.button(T("🔍 اعرض التوصيات", "🔍 Show Recommendations"))
rst = col2.button(T("🔄 إعادة الاختبار", "🔄 Restart"))

if rst:
    st.session_state.clear()
    st.rerun()

# حالة عامة
st.session_state.setdefault("recs", [])
st.session_state.setdefault("ratings", [4, 4, 4])
st.session_state.setdefault("chat_open", False)
st.session_state.setdefault("chat_history", [])

# =========================
# توليد التوصيات + Layer Z
# =========================
if go:
    user_id = "web_user"

    try:
        st.session_state["recs"] = generate_sport_recommendation(answers, lang=lang)[:3]
    except Exception as e:
        st.error(T("خطأ أثناء توليد التوصيات: ", "Error generating recommendations: ") + str(e))
        st.session_state["recs"] = []

    try:
        z = analyze_silent_drivers(answers, lang=lang)
    except Exception:
        z = []

    if z:
        st.subheader(T("🧭 ما يحركك دون أن تدري", "🧭 Your Silent Drivers"))
        for item in z:
            st.write("• " + str(item))
        st.divider()

# =========================
# عرض التوصيات (ثلاثة) + التقييم
# =========================
recs = st.session_state.get("recs", [])
if recs:
    headers_ar = ["🟢 التوصية رقم 1", "🌿 التوصية رقم 2", "🔮 التوصية رقم 3 (ابتكارية)"]
    headers_en = ["🟢 Recommendation #1", "🌿 Recommendation #2", "🔮 Recommendation #3 (Creative)"]

    for i, rec in enumerate(recs[:3]):
        st.subheader(headers_ar[i] if is_ar else headers_en[i])
        st.write(rec)
        st.session_state["ratings"][i] = st.slider(
            "⭐ " + T("قيّم هذه التوصية", "Rate this recommendation"),
            1, 5, value=st.session_state["ratings"][i], key=f"rating_{i}"
        )

    st.divider()
    if st.button(T("🙅‍♂ لم تعجبني التوصيات — افتح محادثة", "🙅‍♂ Not satisfied — open chat")):
        st.session_state["chat_open"] = True

# =========================
# واجهة محادثة شبيهة بالشات (chat UI)
# =========================
if st.session_state.get("chat_open", False):
    st.subheader(T("🧠 محادثة المدرب الذكي", "🧠 AI Coach Chat"))

    for msg in st.session_state["chat_history"]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.write(msg["content"])

    user_msg = st.chat_input(
        T("اكتب ما الذي لم يعجبك أو ما الذي تريد تعديله…", "Tell me what you didn’t like or what to adjust…")
    )

    if user_msg:
        st.session_state["chat_history"].append({"role": "user", "content": user_msg})
        ratings = [st.session_state.get(f"rating_{i}", st.session_state["ratings"][i]) for i in range(3)]

        try:
            reply = start_dynamic_chat(
                answers=answers,
                previous_recommendation=recs[:3],
                ratings=ratings,
                user_id="web_user",
                lang=lang,
                chat_history=st.session_state["chat_history"],
                user_message=user_msg
            )
        except Exception:
            reply = T("تم! سنعدّل الخطة بالتدريج حسب ملاحظتك.",
                      "Got it! We’ll adjust the plan gradually based on your feedback.")

        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)

    st.caption("💬 " + T("يمكنك المتابعة بالدردشة حتى تصل للتوصية المناسبة.", "Keep chatting until the plan feels right."))

st.caption("🚀 Powered by SportSync AI – Your identity deserves its own sport.")
