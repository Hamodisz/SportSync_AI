# -- coding: utf-8 --
import os, json, uuid, urllib.parse
from pathlib import Path
from io import BytesIO

import streamlit as st
import qrcode
from PIL import Image  # noqa: F401  (مطلوبة لـ qrcode.save)

from core.submit_answers_to_queue import submit_to_queue
from core.check_result_ready import check_result

# ===================== إعداد عام =====================
# لو عندك دومين/رندر حطه هنا أو في secrets كـ PUBLIC_BASE، وإلا بيستخدم رابط نسبي
PUBLIC_BASE = st.secrets.get("PUBLIC_BASE", os.getenv("PUBLIC_BASE", "")).rstrip("/")

DATA_DIR = Path("data")
DRAFTS_DIR = DATA_DIR / "drafts"
PENDING_DIR = DATA_DIR / "pending_requests"
READY_DIR = DATA_DIR / "ready_results"
for d in (DATA_DIR, DRAFTS_DIR, PENDING_DIR, READY_DIR):
    d.mkdir(parents=True, exist_ok=True)

def build_share_url(user_id: str, lang: str) -> str:
    qs = f"user_id={urllib.parse.quote(user_id)}&lang={urllib.parse.quote(lang)}"
    return f"{PUBLIC_BASE}/?{qs}" if PUBLIC_BASE else f"?{qs}"

def _draft_path(uid: str) -> Path:
    return DRAFTS_DIR / f"{uid}.json"

def save_draft(user_id: str, answers: dict) -> None:
    try:
        with _draft_path(user_id).open("w", encoding="utf-8") as f:
            json.dump(answers, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_draft(user_id: str) -> dict:
    p = _draft_path(user_id)
    if p.exists():
        try:
            return json.load(p.open("r", encoding="utf-8"))
        except Exception:
            return {}
    return {}

# ===================== لغة + هوية ثابتة بالرابط =====================
params = st.experimental_get_query_params()
lang_from_url = params.get("lang", [None])[0] or "العربية"
lang = st.sidebar.radio("🌐 اختر اللغة / Choose Language",
                        ["العربية", "English"],
                        index=0 if lang_from_url != "English" else 1,
                        key="lang")
is_arabic = (lang == "العربية")

user_id = params.get("user_id", [None])[0]
if not user_id:
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:10]}"
    user_id = st.session_state.user_id
else:
    st.session_state.user_id = user_id

# ثبّت القيم في شريط العنوان دائماً
st.experimental_set_query_params(user_id=user_id, lang=lang)

# ===================== تحميل الأسئلة =====================
question_file = "questions/arabic_questions.json" if is_arabic else "questions/english_questions.json"
with open(question_file, "r", encoding="utf-8") as f:
    questions = json.load(f)

st.title("🎯 توصيتك الرياضية الذكية" if is_arabic else "🎯 Your Smart Sport Recommendation")

# ===================== حالة الواجهة =====================
if "view" not in st.session_state:
    # عند الدخول بالرابط: لو فيه نتيجة جاهزة → اعرضها، لو فيه طلب معلق → انتظار
    result = check_result(user_id)
    if result:
        st.session_state.result = result
        st.session_state.view = "result"
    elif (PENDING_DIR / f"{user_id}.json").exists():
        st.session_state.view = "waiting"
    else:
        st.session_state.view = "quiz"

# حضّر answers (من المسودة إن وجدت)
if "answers" not in st.session_state or not isinstance(st.session_state.answers, dict):
    st.session_state.answers = load_draft(user_id)

def _on_change_any():
    # احفظ المسودة أولاً بأول
    save_draft(user_id, st.session_state.answers)

# ===================== عرض الأسئلة =====================
if st.session_state.view == "quiz":
    st.session_state.answers = st.session_state.answers or {}
    for q in questions:
        q_key = q["key"]
        q_text = q["question_ar"] if is_arabic else q["question_en"]
        q_type = q["type"]
        allow_custom = q.get("allow_custom", False)
        options = q.get("options", [])

        # استرجاع قيمة محفوظة إن وُجدت
        current_val = st.session_state.answers.get(q_text)

        if q_type == "multiselect":
            selected = st.multiselect(q_text, options, default=current_val or [], key=q_key)
            if allow_custom:
                custom_val = st.text_input("✏ " + ("إجابتك الخاصة (اختياري)" if is_arabic else "Your own answer (optional)"),
                                           value="", key=f"{q_key}_custom")
                if custom_val:
                    selected = list(selected) + [custom_val]
            st.session_state.answers[q_text] = selected

        elif q_type == "text":
            st.session_state.answers[q_text] = st.text_input(q_text, value=current_val or "", key=q_key)

    # احفظ بعد بناء كل النموذج
    _on_change_any()

    if st.button("🔍 اعرض التوصيات" if is_arabic else "🔍 Show Recommendations"):
        submit_to_queue(user_id=user_id, answers=st.session_state.answers, lang=lang)
        st.session_state.view = "waiting"
        st.session_state.share_url = build_share_url(user_id, lang)
        st.success("تم إرسال طلبك ✅")
        st.rerun()

# ===================== شاشة الانتظار =====================
elif st.session_state.view == "waiting":
    st.markdown("### ⏳ " + ("تحليل شخصيتك قيد المعالجة..." if is_arabic else "Analyzing your sport identity..."))
    st.info("🔬 " + ("نحن نغوص في أعماق شخصيتك الرياضية..." if is_arabic else "We’re diving into your sport identity..."))

    share_url = st.session_state.get("share_url", build_share_url(user_id, lang))
    st.markdown("📤 هذا رابطك—احفظه وارجع له متى ما بغيت:")
    st.code(share_url)

    # QR (يحتاج PUBLIC_BASE عشان يكون رابط مطلق)
    if PUBLIC_BASE:
        qr = qrcode.make(share_url)
        buf = BytesIO()
        qr.save(buf)
        st.image(buf.getvalue(), width=180, caption="امسح لفتح النتيجة")

    if st.button("🔄 تحديث النتيجة" if is_arabic else "🔄 Refresh Result"):
        result = check_result(user_id)
        if result:
            st.session_state.result = result
            st.session_state.view = "result"
            # إزالة المسودة بعد اكتمال النتيجة (اختياري)
            try: _draft_path(user_id).unlink(missing_ok=True)
            except Exception: pass
            st.rerun()
        else:
            st.warning("… لسه يجهّز")

# ===================== عرض النتيجة =====================
elif st.session_state.view == "result":
    # تأكيد تحميل النتيجة (لو دخلت بالرابط مباشرة)
    result = st.session_state.get("result") or check_result(user_id) or {}
    st.session_state.result = result

    recs = result.get("recommendations", []) or result.get("cards", [])
    if not recs:
        st.warning("لم يتم العثور على نتيجة. ارجع لشاشة الأسئلة.")
    else:
        for i, rec in enumerate(recs):
            st.subheader(["🟢 التوصية رقم 1", "🌿 التوصية رقم 2", "🔮 التوصية رقم 3 (ابتكارية)"][i]
                         if is_arabic else
                         ["🟢 Recommendation 1", "🌿 Recommendation 2", "🔮 Recommendation 3 (Creative)"][i])
            # النص جاهز كـ Markdown من الباك إند
            st.markdown(rec if isinstance(rec, str) else json.dumps(rec, ensure_ascii=False, indent=2))

    st.markdown("---")
    st.caption("🚀 Powered by SportSync AI")

    share_url = st.session_state.get("share_url", build_share_url(user_id, lang))
    st.markdown("📤 رابط مشاركتك:"); st.code(share_url)

    # زر تعديل
    if st.button("✏ عدّل إجاباتك" if is_arabic else "✏ Modify your answers"):
        # امسح النتيجة الجاهزة حتى يُعاد التوليد
        try: (READY_DIR / f"{user_id}.json").unlink(missing_ok=True)
        except Exception: pass
        st.session_state.view = "quiz"
        st.rerun()

# ===================== إعادة الاختبار بالكامل =====================
if st.button("🔄 أعد الاختبار من البداية" if is_arabic else "🔄 Restart"):
    st.session_state.clear()
    st.rerun()
