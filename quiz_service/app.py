# -- coding: utf-8 --
import os, sys, json
import streamlit as st

# أضف مجلد المشروع للجسر مع core/ و analysis/
HERE = os.path.dirname(_file_)
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# نحاول استخدام وحداتك الحقيقية
try:
    from core.backend_gpt import generate_sport_recommendation as _gen_recs
except Exception as e:
    _gen_recs = None

try:
    from analysis.layer_z_engine import analyze_silent_drivers_combined as _analyze_z
except Exception as e:
    _analyze_z = None

try:
    from core.dynamic_chat import start_dynamic_chat as _dynamic_chat
except Exception as e:
    _dynamic_chat = None

# بدائل بسيطة إذا الوحدات أعلاه غير متوفرة
def _fallback_recs(answers, lang="العربية"):
    txt = " ".join([str(v) for v in answers.values()])
    base = [
        "🏃‍♂ الجري الخفيف 3 مرات أسبوعياً" if lang=="العربية" else "Light jogging 3x/week",
        "🚴‍♀ دراجة ثابتة 20 دقيقة يومياً" if lang=="العربية" else "Stationary bike 20min daily",
        "🧘‍♂ يوغا وتعافي + تمارين مقاومة" if lang=="العربية" else "Yoga + light resistance"
    ]
    # لمسة بسيطة حسب الكلمات
    if any(k in txt.lower() for k in ["knee","ركبة","injury","إصابة"]):
        base[0] = "🚶‍♂ مشي + سباحة منخفضة冲" if lang=="العربية" else "Walking + low-impact swimming"
    return base

def _fallback_analyze(answers, lang="العربية"):
    out = []
    if any(len(v)>=3 for v in answers.values() if isinstance(v, list)):
        out.append("تحب التنوع وتستجيب للخيارات المتعددة." if lang=="العربية" else "You like variety and multiple options.")
    out.append("التحفيز العاطفي أهم من الكمال." if lang=="العربية" else "Emotional momentum matters more than perfection.")
    return out

def _fallback_chat(**kwargs):
    lang = kwargs.get("lang","العربية")
    msg = kwargs.get("user_message","")
    if lang=="العربية":
        return f"سمعتك تقول: “{msg}”. خلّنا نعدّل الخطة خطوة بخطوة، نبدا بـ 10 دقايق اليوم."
    return f"I heard you say: “{msg}”. Let’s adjust the plan: start with 10 minutes today."

generate_sport_recommendation = _gen_recs or _fallback_recs
analyze_silent_drivers = _analyze_z or _fallback_analyze
start_dynamic_chat = _dynamic_chat or _fallback_chat

# ================= واجهة =================
st.set_page_config(page_title="SportSync — Quiz", layout="centered")

lang = st.sidebar.radio("🌐 اختر اللغة / Choose Language", ["العربية", "English"])
is_ar = (lang == "العربية")

st.title("🎯 توصيتك الرياضية الذكية" if is_ar else "🎯 Your Smart Sport Recommendation")

# حمل الأسئلة
qfile = "questions/arabic_questions.json" if is_ar else "questions/english_questions.json"
if not os.path.exists(qfile):
    st.error(f"Question file missing: {qfile}")
    st.stop()

with open(qfile, "r", encoding="utf-8") as f:
    questions = json.load(f)

answers = {}
for q in questions:
    key = q.get("key") or q.get("id") or q.get("question_en")[:10]
    text = q["question_ar"] if is_ar else q["question_en"]
    qtype = q.get("type","text")
    allow_custom = q.get("allow_custom", False)
    options = q.get("options", [])

    if qtype == "multiselect":
        sel = st.multiselect(text, options, key=key)
        if allow_custom:
            cust_label = "✏ إجابة حرة (اختياري)" if is_ar else "✏ Free text (optional)"
            cust = st.text_input(cust_label, key=key+"_custom")
            if cust:
                sel.append(cust)
        answers[text] = sel
    else:
        answers[text] = st.text_input(text, key=key)

if st.button("🔍 اعرض التوصيات" if is_ar else "🔍 Show Recommendations", key="btn_recs"):
    user_id = "test_user"

    recs = generate_sport_recommendation(answers, lang=lang) or []
    if isinstance(recs, str):
        recs = [recs]
    while len(recs) < 3:
        recs.append("—")

    drivers = analyze_silent_drivers(answers, lang=lang) or []

    st.markdown("---")
    if drivers:
        st.subheader("🧭 ما يحركك دون أن تدري" if is_ar else "🧭 Your Silent Drivers")
        for d in drivers:
            st.write("• " + str(d))

    for i, rec in enumerate(recs[:3]):
        st.subheader(
            ["🟢","🌿","🔮"][i] + (" التوصية رقم " if is_ar else " Recommendation #") + str(i+1)
        )
        st.write(rec)
        st.slider("⭐ " + ("قيّم هذه التوصية" if is_ar else "Rate this recommendation"),
                  1, 5, 4, key=f"rating_{i}")

    st.markdown("---")
    st.subheader("🧠 تحدث مع المدرب الذكي" if is_ar else "🧠 Talk to the AI Coach")
    prompt = "💬 اكتب ردّك أو سؤالك..." if is_ar else "💬 Type your response or ask a question..."
    user_msg = st.text_input(prompt, key="chat_msg")
    if user_msg:
        ratings = [st.session_state.get(f"rating_{i}", 4) for i in range(3)]
        reply = start_dynamic_chat(
            answers=answers,
            previous_recommendation=recs,
            ratings=ratings,
            user_id=user_id,
            lang=lang,
            chat_history=[],
            user_message=user_msg
        )
        st.markdown("🤖 AI Coach:")
        st.success(reply)

    st.markdown("---")
    st.caption("🚀 Powered by SportSync AI – Your identity deserves its own sport.")
    share = f"https://sportsync.ai/recommendation?lang={lang}&user=test_user"
    st.code(share)

if st.button("🔄 أعد الاختبار من البداية" if is_ar else "🔄 Restart"):
    st.session_state.clear()
    st.rerun()
