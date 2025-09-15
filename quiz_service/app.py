# -- coding: utf-8 --
import os, sys, json, time, textwrap
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

# (اختياري) ستريم حقيقي إن وفّرته لاحقًا
try:
    from core.dynamic_chat import start_dynamic_chat_stream  # يجب أن يُرجع generator للنص/التوكِنز
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

# =========================
# إعدادات واجهة + لغة
# =========================
st.set_page_config(page_title="SportSync — Quiz", page_icon="🎯", layout="centered")
lang = st.sidebar.radio("🌐 اختر اللغة / Choose Language", ["العربية", "English"], index=0)
is_ar = (lang == "العربية")
T = (lambda ar, en: ar if is_ar else en)

# ✅ تحكم بالتجربة
with st.sidebar.expander(T("⚙ إعدادات العرض", "⚙ Display Settings"), expanded=True):
    LIVE_TYPING = st.checkbox(T("إظهار كتابة حيّة (typewriter)", "Show live typing (typewriter)"), value=True)
    SHOW_THINKING = st.checkbox(T("إظهار مراحل التفكير", "Show thinking stages"), value=True)
    TYPE_SPEED_MS = st.slider(T("سرعة الكتابة (ملّي ثانية/حرف)", "Typing speed (ms/char)"), 1, 30, value=6)

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
    """context manager بسيط لمراحل التفكير."""
    class _Dummy:
        def _enter_(self):
            return self
        def _exit_(self, *exc):
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
        # بديل قديم
        class _Alt:
            def _init_(self):
                self.box = st.empty()
                self.lines = []
                self.box.write("\n".join(str(x) for x in self.lines))
            def _enter_(self): return self
            def _exit_(self, *exc): return False
            def write(self, text): 
                self.lines.append(text)
                self.box.write("\n".join(str(x) for x in self.lines))
            def info(self, text): self.write("ℹ " + text)
            def warning(self, text): self.write("⚠ " + text)
            def success(self, text): self.write("✅ " + text)
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

# =========================
# توليد التوصيات + Layer Z (مع مراحل تفكير)
# =========================
if go:
    user_id = "web_user"

    with status_steps(SHOW_THINKING) as stat:
        try:
            if SHOW_THINKING: stat.info(T("تحليل الإجابات…", "Analyzing answers…"))
            # ➊ توليد التوصيات
            raw_recs = generate_sport_recommendation(answers, lang=lang)
            st.session_state["recs"] = raw_recs[:3] if isinstance(raw_recs, list) else []
            if SHOW_THINKING: stat.info(T("مواءمة مع محاور Z…", "Aligning with Z-axes…"))
        except Exception as e:
            st.error(T("خطأ أثناء توليد التوصيات: ", "Error generating recommendations: ") + str(e))
            st.session_state["recs"] = []

        # ➋ Layer Z
        try:
            z = analyze_silent_drivers(answers, lang=lang) or []
        except Exception:
            z = []
        st.session_state["z_drivers"] = z

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
        st.write("• " + str(item))
    st.divider()

# =========================
# عرض التوصيات (ثلاثة) + التقييم (مع كتابة حيّة)
# =========================
recs = st.session_state.get("recs", [])
if recs:
    headers_ar = ["🟢 التوصية رقم 1", "🌿 التوصية رقم 2", "🔮 التوصية رقم 3 (ابتكارية)"]
    headers_en = ["🟢 Recommendation #1", "🌿 Recommendation #2", "🔮 Recommendation #3 (Creative)"]
    rendered_text = []

    for i, rec in enumerate(recs[:3]):
        st.subheader(headers_ar[i] if is_ar else headers_en[i])
        ph = st.empty()
        text_to_show = str(rec)

        # كتابة حيّة للتوصية
        typewriter_write(ph, text_to_show, TYPE_SPEED_MS)
        rendered_text.append(text_to_show)

        st.session_state["ratings"][i] = st.slider(
            "⭐ " + T("قيّم هذه التوصية", "Rate this recommendation"),
            1, 5, value=st.session_state["ratings"][i], key=f"rating_{i}"
        )

    st.divider()
    cA, cB = st.columns([1,1])
    if cA.button(T("🙅‍♂ لم تعجبني — افتح محادثة", "🙅‍♂ Not satisfied — open chat")):
        st.session_state["chat_open"] = True

    # تنزيل التوصيات كنص
    if dl and rendered_text:
        all_text = "\n\n".join(str(x) for x in rendered_text)
        st.download_button(
            label=T("⬇ تنزيل كملف TXT", "⬇ Download as TXT"),
            data=all_text.encode("utf-8"),
            file_name="sportsync_recommendations.txt",
            mime="text/plain"
        )

# =========================
# واجهة محادثة شبيهة بالشات (chat UI) + كتابة حيّة/ستريم
# =========================
if st.session_state.get("chat_open", False):
    st.subheader(T("🧠 محادثة المدرب الذكي", "🧠 AI Coach Chat"))

    # عرض السجل القديم
    for msg in st.session_state["chat_history"]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    user_msg = st.chat_input(
        T("اكتب ما الذي لم يعجبك أو ما الذي تريد تعديله…", "Tell me what you didn’t like or what to adjust…")
    )

    if user_msg:
        # أضف رسالة المستخدم للسجل
        st.session_state["chat_history"].append({"role": "user", "content": user_msg})
        typewriter_chat("user", user_msg, TYPE_SPEED_MS)

        # حضّر معطيات المكالمة
        recs_for_chat = st.session_state.get("recs", [])[:3]
        ratings = [st.session_state.get(f"rating_{i}", st.session_state["ratings"][i]) for i in range(3)]

        # ردّ المساعد — ستريم حقيقي إن توفر، وإلا كتابة حيّة للناتج النهائي
        if start_dynamic_chat_stream is not None:
            # ستريم حقيقي (generator)
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
                        user_message=user_msg
                    ):
                        buf.append(chunk)
                        if LIVE_TYPING:
                            ph.markdown("".join(str(x) for x in buf))
                    reply = "".join(str(x) for x in buf).strip()
                except Exception:
                    reply = T("تم! سنعدّل الخطة بالتدريج حسب ملاحظتك.",
                              "Got it! We’ll adjust the plan gradually based on your feedback.")
                st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        else:
            # نداء عادي ثم كتابة حيّة
            try:
                reply = start_dynamic_chat(
                    answers=answers,
                    previous_recommendation=recs_for_chat,
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
            typewriter_chat("assistant", reply, TYPE_SPEED_MS)

    st.caption("💬 " + T("تقدر تواصل الدردشة لين توصّل لهويتك الرياضية اللي تحسها ملكك.",
                          "Keep chatting until the plan feels like yours."))

st.caption("🚀 Powered by SportSync AI — Your identity deserves its own sport.")
