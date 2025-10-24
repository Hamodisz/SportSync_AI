# -- coding: utf-8 --
"""Rich analytical fallback recommendations for SportSync."""
from __future__ import annotations

if __name__ == '__main__':  # allow running as script
    import sys
    from pathlib import Path as _Path
    sys.path.append(str(_Path(__file__).resolve().parent.parent))

import hashlib
import json
import os
import random
import re
from datetime import datetime
from typing import Any, Dict, List, Sequence, Optional

try:  # Optional LLM client; fallback works without it.
    from core.llm_client import get_client_and_models, make_llm_client, pick_models, chat_once  # type: ignore
except Exception:  # pragma: no cover - LLM unavailable
    get_client_and_models = None
    make_llm_client = None
    pick_models = None
    chat_once = None
from core.user_logger import log_event


BANNED_TERMS = ["خسارة الوزن", "حرق الدهون", "سعرات", "وزن", "خطة أسبوعية", "دقيقة", "دقائق", "ساعة", "ساعات"]

ARACHETYPE_DATA: Dict[str, Dict[str, Any]] = {}
LAST_RECOMMENDER_SOURCE = "unset"


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[\w\u0600-\u06FF]+", text.lower())


def _jaccard(a: str, b: str) -> float:
    set_a = set(_tokenize(a))
    set_b = set(_tokenize(b))
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _stable_json(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(data)


def _session_id_from_answers(answers: Dict[str, Any]) -> str:
    for key in ("_session_id", "session_id", "sessionId"):
        if key in answers and answers[key]:
            return str(answers[key])
    return "anon"


def _extract_identity(answers: Dict[str, Any]) -> Dict[str, float]:
    text = (str(answers) or "").lower()
    def flag(keys: Sequence[str]) -> float:
        return 0.6 if any(k in text for k in keys) else 0.45

    identity = {
        "tactical": flag(["تكتي", "تحليل", "استراتيجية", "strategy", "smart"]),
        "sensory": flag(["هدوء", "تنفس", "سكون", "حس", "calm", "breath"]),
        "adventure": flag(["مغام", "استكشاف", "explore", "طبيعة"]),
        "achievement": flag(["تحد", "إنجاز", "تفوق", "win"]),
        "social": flag(["فريق", "جماعي", "مجموعة", "team", "friends"]),
        "solo": flag(["فردي", "لوحد", "solo", "انعزال"]),
        "indoor": flag(["داخل", "indoor", "استوديو", "صالة"]),
        "outdoor": flag(["هواء", "outdoor", "حديقة", "سماء"]),
    }
    return identity


def _drivers(identity: Dict[str, float], lang: str) -> List[str]:
    ar = lang in ("العربية", "ar")
    lines: List[str] = []
    if identity["tactical"] >= 0.58:
        lines.append("تحب قراءة المشهد قبل الحركة وتحتفظ بخطط سرية في ذهنك." if ar else "You read the scene before moving and keep quiet strategies in mind.")
    if identity["sensory"] >= 0.58:
        lines.append("تهدأ عندما تراقب أنفاسك وتلتقط الإشارات الصامتة من المكان." if ar else "You settle when you listen to your breath and catch the room’s silent cues.")
    if identity["adventure"] >= 0.58:
        lines.append("تنجذب للمسارات الجديدة وتعتبر كل زاوية فرصة لقصّة اكتشاف." if ar else "You are pulled toward new routes and treat each corner as an exploration story.")
    if identity["achievement"] >= 0.58:
        lines.append("يبهرك الشعور بإنجاز يحمل توقيعك الشخصي دون الحاجة للضجيج." if ar else "You cherish wins that carry your signature without noise.")
    if identity["social"] >= 0.58:
        lines.append("تتلون طاقتك مع الفريق وتستمتع حين تتحول الجلسة إلى حوار حركي." if ar else "Your energy blooms with a team when every drill becomes a kinetic dialogue.")
    if identity["solo"] >= 0.58:
        lines.append("تزدهر في اللحظات الهادئة التي تسمع فيها صوتك الداخلي بوضوح." if ar else "You flourish in calm moments where your inner voice is the guide.")
    if identity["indoor"] >= 0.58:
        lines.append("تميل إلى البيئات المضبوطة التي يمكنك إعادة تشكيلها حسب مزاجك." if ar else "You lean toward controlled environments you can reshape to fit your mood.")
    if identity["outdoor"] >= 0.58:
        lines.append("يعجبك الهواء المفتوح لأنه يحرر الخيال وينعش خطواتك." if ar else "Open air frees your imagination and refreshes your stride.")
    if not lines:
        lines.append("تحب التعرف على نفسك عبر تجربة حركية تنبض بالدهشة." if ar else "You enjoy discovering yourself through surprising motion.")
    return lines


def _drivers_sentence(drivers: List[str], lang: str) -> str:
    if not drivers:
        return ""
    if lang in ("العربية", "ar"):
        if len(drivers) == 1:
            return drivers[0]
        return "؛ ".join(drivers[:-1]) + "؛ " + drivers[-1]
    if len(drivers) == 1:
        return drivers[0]
    if len(drivers) == 2:
        return f"{drivers[0]} and {drivers[1]}"
    return ", ".join(drivers[:-1]) + ", and " + drivers[-1]


# Archetype content ---------------------------------------------------------

def _archetype_data() -> Dict[str, Dict[str, Any]]:
    ar = "ar"
    en = "en"
    data: Dict[str, Dict[str, Any]] = {
        "tactical_immersive": {
            "score": lambda ident: ident["tactical"] + 0.35 * ident["achievement"],
            "titles": {
                ar: ["Tactical Immersive Combat", "سرد تكتيكي حي"],
                en: ["Tactical Immersive Combat", "Live Tactical Narrative"],
            },
            "silent": {
                ar: [
                    "{drivers}. هذا الأثر الهادئ يمنحك شعورًا بأنك قائد خلف الكواليس يقرأ المشهد من الأعلى قبل أن يلامس الأرض. تحب أن تتذوق لحظة الترقب تلك، حيث تتداخل خرائط ذهنية دقيقة وتلتقط عيناك أضعف الإشارات. كلما طال الصمت الأولي ازداد وضوح الهدف وكأنك تبني سيناريو سريًا لا يراه سواك.",
                    "{drivers}. تشعر بأن عقلك هو غرفة عمليات مصغّرة، تسمع فيها وقع الخطوات القادمة قبل وصولها، وتمنحك المسافة ما يكفي لإعادة ترتيب القطع. هذا المحرك الصامت يذكّرك بأن الذكاء ليس ادعاءً بل حضور مستتر ينتظر اللحظة المناسبة ليعلن نفسه."],
                en: [
                    "{drivers}. The quiet impact makes you feel like a director behind the curtain, surveying the scene before anything touches the floor. You savour that moment of anticipation where intricate mental maps overlap and your eyes register faint signals. The longer the initial silence, the clearer the mission becomes, as if you are scripting a secret story.",
                    "{drivers}. Your mind behaves like a compact command room that hears approaching steps before they arrive, gifting you a chance to reorganise the board. This silent engine reminds you that intelligence is not a show but a subtle presence waiting for the right cue."],
            },
            "what": {
                ar: [
                    "هذه الهوية تجمعك مع مساحات تحاكي ألعاب التجسس والأفلام الذهنية. تدخل قاعة أو بيئة واقع افتراضي تتغير مع كل خطوة، فتجد مسارات ضوء تفتح وتغلق، وأصواتًا تحرك خيالك الاستراتيجي. يُطلب منك تصميم فخاخ ذهنية أو تدوين ملاحظات عن إيماءاتك، لتشعر أن التدريب نفسه قصة غامرة كتبتها بنفسك." ,
                    "تجد نفسك في عالم يدمج التكنولوجيا بالحركة: غرف مغلقة قابلة لإعادة التشكيل، وأجهزة تراقب زاوية نظرك لتعطيك ردود فعل ذكية. يتم تشجيعك على بناء منظومات خداع بصري، واختبار سيناريوهات متعددة، وكأنك تحيي رواية متجددة في كل مرة."],
                en: [
                    "This identity pairs you with spaces that echo stealth games and cerebral films. You enter a hall or VR environment that morphs with each step, witnessing beams of light opening and closing while sounds stir your strategic imagination. You are invited to engineer mental traps and journal your gestures so the practice itself becomes a story you authored.",
                    "You inhabit a realm that fuses technology with deliberate movement: modular rooms, sensors tracking your gaze, and responsive cues. You are encouraged to craft optical misdirection and rehearse multiple scenarios, as though you revive a fresh narrative each time."],
            },
            "why": {
                ar: [
                    "لأنك تبحث عن متعة السيطرة دون صخب، ولأن القرارات المحسوبة تمنحك راحة داخلية لا تشبه فوزًا سريعًا. هذا الأسلوب يحترم رغبتك في اختبار ذكائك الحركي، ويمنحك مساحة لتجريب جرأة جديدة كل مرة دون فقدان الهيبة. تشعر بأنك تخلق لغة خاصة بين الجسد والعقل." ,
                    "تنجذب لهذا المسار لأنه يسمح لك بالاحتفاظ بأناقتك الفكرية أثناء الحركة. توازن بين الحذر والاندفاع، وتستمتع حين ترى التخطيط يتجسد على الأرض. ليس الهدف إثارة الإعجاب بل بناء يقين داخلي بأن ذكاءك قابل للترجمة إلى حركة ملموسة."],
                en: [
                    "Because you crave mastery without noise and calculated decisions soothe you more than quick wins. This approach honours your desire to challenge your kinetic intellect, letting you test bold ideas without losing grace. You end up crafting a personal language between mind and body.",
                    "You lean toward this path because it lets you keep intellectual elegance while moving. You balance caution and momentum and enjoy watching strategy take physical form. The goal is not applause but the inner certainty that your intelligence can migrate into motion."],
            },
            "real": {
                ar: [
                    "في الواقع قد تبدأ بدخول مساحة شبه مظلمة تضيء أجسامها الذكية بمجرد أن تستشعر خطواتك. يتم تمرير أهداف مرئية وصوتية أمامك، فتتعلم استخدام نظراتك وإشارات كتفك قبل أي حركة. كل حصة تنتهي بحوار قصير مع ذاتك، تستعرض فيه ما التقطته حواسك من تفاصيل." ,
                    "ستختبر جلسات تتدرج من مشي مترقب إلى مواجهات افتراضية سريعة، مع مجال لإعادة التجربة من زوايا مختلفة. المدرب أو التطبيق يصغي لأسئلتك ويعيد بناء المشهد بناءً على فضولك، لتخرج بقصة جديدة في كل مرة."],
                en: [
                    "In reality you may step into a semi-dark chamber where responsive surfaces glow once they sense your stride. Visual and audio targets sweep past, teaching you to deploy your gaze and shoulder cues before any bigger move. Each session ends with an inner debrief about the details your senses captured.",
                    "You experience sessions evolving from cautious walks to brisk virtual duels, always leaving room to replay from new angles. A coach or intelligent system listens to your questions and rebuilds the scene according to your curiosity, so every outing closes with a fresh storyline."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nتخيل موقفًا حقيقيًا شعرت فيه بأنك تريد قول شيء ولكنك التزمت الصمت لتحلل التفاصيل. اكتب ذلك في سطر واحد، ثم حوّله إلى مشهد تدريبي تستخدم فيه نفس المشاعر ولكن بحركة صغيرة، مثل التفاف الرأس أو خطوة للأمام. كلما أعدت المشهد وجدت زاوية جديدة تضاف إلى لغتك البدنية." ,
                    "🔄 ابدأ من هنا\nاستعد ذكرى موقف استحضرت فيه الجرأة الذهنية، واسأل نفسك كيف تبدو لو تحولت إلى حركة. مارس تصوير السيناريو بعينيك وأنت تمشي ببطء في الغرفة، ثم امنح جسدك إشارة ليترجم تلك الصورة. المهم أن تبقي الفكرة حية وتشعر بأن الخيال يسبق الفعل بثوانٍ طويلة."],
                en: [
                    "🔄 ابدأ من هنا\nRecall a real moment when you chose silence to analyse the details. Write it in one line, then convert it into a training vignette where you reuse the same emotions with a small gesture, like a head tilt or a forward step. Each retelling reveals a new angle in your body language.",
                    "🔄 ابدأ من هنا\nBring back a memory where mental courage guided you and ask how it would look if expressed physically. Practice drawing the scene with your eyes while strolling slowly, then let your body translate the idea. Keep the concept alive and let imagination precede action by several heartbeats."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nإذا تحوّل التدريب إلى صخب، أطفئ بعض الأضواء، أو بدّل الخلفية الصوتية إلى حوار هادئ. ذكّـر نفسك أن الذكاء قابل للتجديد، وأن الاستراحة الفكرية جزء من رحلتك. استعن بشريك يفهم شغفك كي يمدك بقراءات جديدة للمشهد." ,
                    "👁️‍🗨️ ملاحظات\nراقب متى تشعر بأن الخيال سبق الحركة، وسجل ذلك في مفكرة صغيرة. قد تكشف لاحقًا أن أفضل الأفكار أتت من لحظات الظل وليس من الضوء المباشر. امنح جسدك حرية إعادة ترتيب التسلسل كما يشاء دون توقعات صارمة."],
                en: [
                    "👁️‍🗨️ ملاحظات\nIf the training turns noisy, dim some lights or switch to a quiet dialogue soundtrack. Remind yourself that intelligence renews itself and that mental pauses are part of the journey. Invite a partner who grasps your passion to offer new readings of each scene.",
                    "👁️‍🗨️ ملاحظات\nNotice when imagination leaps ahead of the move and jot it in a small notebook. You may later find that the finest ideas emerged from shadow rather than direct glare. Let your body reorder the storyline freely without strict expectations."],
            },
        },
        "stealth_flow": {
            "score": lambda ident: ident["sensory"] + 0.25 * ident["solo"],
            "titles": {
                ar: ["Stealth-Flow Missions", "انسياب الظلال الهادئ"],
                en: ["Stealth-Flow Missions", "Silent Flow Odyssey"],
            },
            "silent": {
                ar: [
                    "{drivers}. تحب أن تستمع إلى الصمت وهو يتنفس، وتفضل اللحظات التي ينساب فيها الهواء حولك دون أن يشعر بك أحد. هنا يصبح الهدوء محركًا حقيقيًا؛ يمنحك ثقة أن كل خطوة متوازنة مع نبضك الداخلي، وأنك تستطيع التلاعب بالمشهد من دون أن تفسد صفاءه." ,
                    "{drivers}. تتعامل مع الصمت كأداة فنية، فأنت لا تهرب منه بل تدعوه ليصبح شريكًا في الحركة. كلما تتبعت أنفاسك بعمق، انفتحت أمامك طبقات جديدة من الإحساس لا تحتاج إلى ضوضاء كي تثبت حضورها."],
                en: [
                    "{drivers}. You enjoy hearing silence breathe and prefer when air glides around you without drawing attention. Calm transforms into a genuine engine, gifting you the confidence that every step mirrors your pulse and lets you sculpt the scene gently.",
                    "{drivers}. You treat stillness as an artistic tool: you do not run from it, you invite it to partner with your movement. Each deep breath unveils new layers of sensation that never require noise to prove their existence."],
            },
            "what": {
                ar: [
                    "هذه الهوية تقودك إلى ممرات مظللة، غرف استوديو بعناية سينمائية، أو بيئات واقع افتراضي تلعب بالضوء والصوت لتضعك في حالة حلم يقظ. تتحسس الجدران، تغير اتجاهك كي تكتشف الانسياب المناسب، وتتعلم كيف تُذيب حركتك داخل المكان بدلًا من فرضها." ,
                    "ستتنقل بين منصات لينة، أقمشة معلقة، ودوائر إضاءة متدرجة، وكأنك ترقص مع ظلّك الشخصي. تُشجع على رسم مسارات متعرجة، حفر توقيعك على الأرض بلمسات خفيفة، والاستماع للفراغ وهو يجاوب على خطواتك."],
                en: [
                    "This identity ushers you through shaded hallways, studio rooms curated like slow-burn cinema, or VR landscapes that toy with light and sound to place you in a waking dream. You feel surfaces, alter direction to discover the right flow, and learn to dissolve your motion inside the space instead of imposing it.",
                    "You will move among soft platforms, suspended fabrics, and graduated light halos as if you dance with your own silhouette. You are encouraged to sketch winding trajectories, leave a delicate signature on the floor, and listen to empty space responding to your steps."],
            },
            "why": {
                ar: [
                    "لأنك تبحث عن تجربة تنغمس فيها حواسك من دون ضجيج خارجي، ولأنك تثمّن اللحظة التي يتحول فيها الجسد إلى ريشة ترسم إحساسًا يصعب وصفه بالكلمات. هذا المسار يمنحك سياقًا تستعرض فيه قدرتك على البقاء هادئًا حتى وأنت تتحرك بقوة." ,
                    "أنت تميل للهدوء الذي يحمل سرًا؛ لا تحتاج إلى صراخ كي تثبت وجودك، لكنك ترغب في ترك أثر ناعم يراه من يدقق. هنا يتم الاحتفاء برغبتك في الانغماس الداخلي، وتُمنح فرصة لتوليد جمال من مجرّد همسة حركة."],
                en: [
                    "Because you seek an experience where senses immerse without external commotion, and you value the moment when your body becomes a brush painting emotions words cannot contain. This path offers a context to showcase how calm remains even when you move powerfully.",
                    "You gravitate toward quiet that holds secrets; you do not need loud declarations yet still wish to leave a soft trace for attentive eyes. Here your desire for inner immersion is celebrated and you gain room to create beauty from a whisper of motion."],
            },
            "real": {
                ar: [
                    "في الواقع ستتعرف على تقنيات تجعل كل حصة مختلفة: أحيانًا تُطفأ الأضواء ويستعاض عنها بمصادر ضوء خافتة، وأحيانًا يُضاف بخار خفيف ليكشف مسار الهواء حولك. تعبر من وضعية لوقفة ثم إلى انزلاق، وتشعر أن كل تغير بسيط يفتح بوابة جديدة." ,
                    "قد تبدأ بجلسة استشعار تنصت فيها إلى نبضك، ثم تنتقل إلى مسار يجمع التوازن مع التحول السريع، دون أن تفقد إحساسك بالأمان. المدرب أو التطبيق يشجعك على استكشاف تفاصيل ملمس الأرض، ورصد كيف يستجيب جسدك لكل انعطافة."],
                en: [
                    "In practice you discover techniques that keep each session unique: sometimes lights dim to mere glows, other times a soft mist reveals air currents around you. You shift from stillness to poised stances to gliding sequences, realising that every subtle change opens a new portal.",
                    "You might begin with a sensing routine listening to your pulse, then ease into a pathway mixing balance with quick shifts without losing your sense of safety. A coach or app nudges you to notice textures underfoot and chart how your body answers each turn."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nاختر زاوية في غرفتك وأطفئ الإضاءة القوية، ثم دع شعاعًا صغيرًا يحدد مساحة اللعب. تحرك ببطء، وكأنك تكتب رسالة غير مرئية، ولاحظ كيف يتغير الإحساس عندما تقرّب يدك من الضوء أو تبتعد عنه. سجّل شعورك بعد التجربة لتعرف أي عنصر فتح لك الباب." ,
                    "🔄 ابدأ من هنا\nضع قطعة قماش خفيفة على كتفك وتحرك داخل الغرفة مع مراقبة تفاعل القماش مع الهواء. عندما تسمع حركته أو تراه يتمايل، استثمر تلك اللحظة لصنع إيقاعك الداخلي. الفكرة أن تجعل التفاصيل الصغيرة تعلن حضورك بدلاً من رفع الصوت."],
                en: [
                    "🔄 ابدأ من هنا\nPick a corner in your room, dim bright lights, and let a single glow define the playground. Move slowly as if writing an invisible letter and observe how sensation changes when your hand nears or leaves the beam. Journal the feeling afterwards to know which element opened the gate.",
                    "🔄 ابدأ من هنا\nPlace a light fabric on your shoulder and wander through the room while watching how it responds to the air. When you hear or see it sway, use that instant to craft your internal rhythm. The idea is to let tiny details announce your presence instead of raising the volume."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nلا تجعل التجربة تنحبس في مكان واحد؛ جرّب الروائح أو الخلفيات الموسيقية الهادئة أو تغيير درجة الحرارة قليلاً. حافظ على دفتر تسجل فيه اللحظات التي شعرت فيها أن جسدك اختفى داخل المشهد وأعد قراءتها حين تبحث عن إلهام جديد." ,
                    "👁️‍🗨️ ملاحظات\nإذا شعرت أن الانسياب أصبح آليًا، بدّل إيقاعات القدمين أو أدخل عنصرًا بصريًا جديدًا مثل خيط ضوء أو مرآة صغيرة. احتفل بكل مرة يذكرك فيها جسدك أن الصمت لا يعني الغياب بل الاستعداد لخطوة أجمل."],
                en: [
                    "👁️‍🗨️ ملاحظات\nDo not let the experience lock into one room; experiment with scents, hushed background music, or slight temperature shifts. Keep a notebook of moments when your body felt absorbed into the scene and revisit it when you need inspiration.",
                    "👁️‍🗨️ ملاحظات\nIf the flow turns automatic, alter foot rhythms or introduce a new visual element like a thin beam of light or a small mirror. Celebrate each time your body reminds you that silence is not absence but readiness for a finer move."],
            },
        },
        "urban_exploration": {
            "score": lambda ident: ident["adventure"] + 0.25 * ident["outdoor"],
            "titles": {
                ar: ["Urban Exploration Athletics", "رحلة الاستكشاف الحضري"],
                en: ["Urban Exploration Athletics", "Urban Discovery Circuit"],
            },
            "silent": {
                ar: [
                    "{drivers}. تشعر أن المدينة تناديك باسمك السري، وتمنحك أزقتها فرصة لإعادة كتابة العلاقة بينك وبين الحركة. صمتك الداخلي يتحول إلى بوصلة تستشعر بها أحجار الأرصفة وروائح المقاهي، فتدرك أن كل منعطف يخفي لعبة جديدة." ,
                    "{drivers}. لديك حس المغامر الذي يعرف كيف يختار لحظته، فلا تهرول بلا هدف ولا تتوقف بلا معنى. كل ما حولك يتحول إلى خريطة حية تتجاوب مع خطواتك الشعرية."],
                en: [
                    "{drivers}. You hear the city calling your hidden name and offering its alleyways as a canvas to rewrite your relationship with motion. Your inner quiet becomes a compass sensing pavement textures and café aromas, revealing a new game at every turn.",
                    "{drivers}. You possess the explorer’s instinct to choose the right moment—never rushing without purpose nor halting without intention. Everything around you becomes a living map that responds to your poetic stride."],
            },
            "what": {
                ar: [
                    "هذا الأركتايب يحول الأحياء إلى ملعب قصصي: جدران يمكن التسلق عليها، حواف ضيقة للتوازن، وأسقف تمارس عليها باركورًا مصممًا بعناية. تتعامل مع أعمدة الإنارة كأنها أصدقاء قدامى، وتحول الأرصفة إلى متاهة ممتعة من الانعطافات الذكية." ,
                    "ستكتشف أن كل شارع يخبئ مستوى جديدًا من المغامرة؛ ربما تنظم جولة جيوكاشينغ حركية مع أصدقاء، أو ترسم مساراتك على خريطة رقمية، فتشعر أن المدينة تستجيب لخيالك وتعيد تشكيل نفسها حولك."],
                en: [
                    "This archetype turns neighbourhoods into narrative playgrounds: walls for scaling, narrow edges for balance, and rooftops for carefully designed parkour. Streetlamps feel like longtime companions and sidewalks morph into delightful mazes of clever turns.",
                    "You discover that every street hides a fresh layer of adventure: perhaps you host a kinetic geocaching tour with friends or draw your paths on a digital map, sensing the city reshape itself around your imagination."],
            },
            "why": {
                ar: [
                    "لأنك تعشق الشعور بأن العالم مفتوح بلا قيود؛ تحب الحرية التي لا تحتاج تصريحًا، وتفرح حين يتحول الطريق اليومي إلى قصة أنت بطلها. هذا الأسلوب يمنحك صداقة مع المكان ويذكرك بأن الإلهام لا يعيش في قاعات مغلقة فقط." ,
                    "تفضل المغامرة التي تحمل معنى، لا مجرد حركة عشوائية. تستمتع بتوثيق اكتشافاتك ومشاركتها، وتشعر بأن الهوية الحركية تتوسع كلما أضفت تفاصيل جديدة إلى خارطة ذاكرتك."],
                en: [
                    "Because you love the sensation of a world without walls; you celebrate permissionless freedom and delight when daily routes become stories that star you. This approach befriends the city and reminds you that inspiration does not live solely in closed studios.",
                    "You prefer adventure with meaning, not random motion. You enjoy documenting discoveries and sharing them, feeling your movement identity grow whenever you add fresh details to your memory map."],
            },
            "real": {
                ar: [
                    "في التطبيق الواقعي ستعمل على مسح بصري للحي الذي تحبه، تدوّن النقاط التي يمكن القفز منها أو الالتفاف حولها، ثم تعود في أوقات مختلفة لتلاحظ تغيّر الإحساس. ربما تضيف عناصر فنية مثل خيوط قماش أو رسومات طباشير لتجعل المكان يتفاعل معك." ,
                    "قد تدمج بين الأسطح المرتفعة والجسور القصيرة والحدائق الصغيرة، لتخلق سلسلة مشاهد متتابعة. كل مشهد يشجعك على استخدام جسدك بأسلوب جديد، مثل التحرك جانبيًا أو الانحناء لالتقاط تفصيلة لم تلاحظها من قبل."],
                en: [
                    "In practice you visually survey a favourite district, noting points for vaults or sweeping turns, then revisit at different times to observe changing sensations. You might add artistic touches like fabric trails or chalk sketches so the space converses with you.",
                    "You may weave together raised platforms, short bridges, and pocket parks to craft sequential scenes. Each scene nudges you to use your body differently, perhaps moving sideways or bending to catch a detail you had never seen."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nاختر شارعًا قصيرًا تعرفه، وامشِ فيه ببطء مع التقاط ثلاث صور ذهنية لأماكن تجذبك. في اليوم التالي عد إلى أحد هذه الأماكن وابحث عن طريقة للتفاعل معه، كمحاولة لمس الحافة أو التحرك حوله بشكل فني. سجّل شعورك لتبني عليه مغامرة أطول." ,
                    "🔄 ابدأ من هنا\nاحمل معك خريطة ورقية صغيرة وارسم عليها مسارًا شاعريًا يربط بين نقطتين تحبهما. أثناء السير اتبع الخريطة وكأنك تمتلك سرًا، واستمتع بكل مفاجأة تظهر لك. استمع لقلبك حين يقترح انعطافة جديدة ولو للحظات."],
                en: [
                    "🔄 ابدأ من هنا\nPick a short street you know and walk it slowly while capturing three mental snapshots of spots that attract you. Return the next day to one location and find a way to interact with it—perhaps touching an edge or circling it artistically. Record the feeling and build a longer adventure from there.",
                    "🔄 ابدأ من هنا\nCarry a small paper map and sketch a poetic route connecting two places you adore. Follow it as if holding a secret, enjoying every surprise along the way. Listen to your heart whenever it suggests a new turn, even for a brief moment."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nحافظ على سلامتك باختيار مواقع مدروسة واستشارة صديق يرافقك في البداية. اصنع أرشيفًا بصريًا لما تكتشفه، فربما تلهم تجربتك آخرين يبحثون عن طريقة جديدة للتواصل مع المدينة." ,
                    "👁️‍🗨️ ملاحظات\nغيّر أوقاتك بين الصباح والمساء لترى كيف تتغير الشخصية الحسية للشارع. لا تستعجل توثيق كل شيء؛ دع بعض الأسرار محفوظة لك وحدك كي تظل الرحلة مدهشة."],
                en: [
                    "👁️‍🗨️ ملاحظات\nStay safe by choosing thoughtful spots and inviting a friend for early explorations. Build a visual archive of what you discover; your journey may inspire others seeking a fresh relationship with the city.",
                    "👁️‍🗨️ ملاحظات\nSwap between morning and evening to feel how the street’s sensory character shifts. Do not rush to document everything; leave a few secrets for yourself so the journey keeps its sparkle."],
            },
        },
        "precision_duel": {
            "score": lambda ident: ident["tactical"] + 0.25 * ident["solo"],
            "titles": {
                ar: ["Precision Duel Sports", "منازلة الدقة الهادئة"],
                en: ["Precision Duel Sports", "Quiet Precision Duels"],
            },
            "silent": {
                ar: [
                    "{drivers}. تميل إلى اللحظة التي يتوقف فيها الزمن قبل الإطلاق، وتشعر بأن أعصابك تملك لغة خاصة لا يمكن سماعها. تحب أن تتذوق ثباتك الداخلي قبل أن تتحول الفكرة إلى حركة، وكأنك تكتب معادلة لا تُحل إلا عندما تنفذها." ,
                    "{drivers}. تنتظر لحظة اللمسة النهائية كما ينتظر الرسام ضربته الأخيرة، تراجع زوايا كتفك وتستمع للهدوء الذي يسبق اللقطة. يهمك أن يبقى الذكاء حاضرًا حتى في أهدأ لحظاتك."],
                en: [
                    "{drivers}. You linger in the moment when time halts before release, sensing that your nerves speak a private language. You savour inner steadiness before an idea becomes motion, as if writing an equation solved only in execution.",
                    "{drivers}. You await the finishing touch like a painter waits for the final stroke, reviewing shoulder angles and enjoying the hush preceding the cue. Keeping intellect active even during stillness matters to you."],
            },
            "what": {
                ar: [
                    "هذه الهوية تجمع الرماية الهادئة مع المبارزة المتزنة، وتمنحك فرصة لتشعر بأن جسدك آلة دقيقة تستجيب لأقل إشارة. تتحرك في مناطق تتخذ شكل مسار شرف، حيث تراقب الكتفين والقدمين كما لو كنت قائد فرقة موسيقية." ,
                    "ستجد أن أدواتك – سواء كانت قوسًا أو سيفًا أو مضربًا – تتحول إلى امتداد لفكرك. تتعلم كيف تطلق الحركة من دون تشنج، وتحتفي بكل ضربة متقنة كأنها توقيع خاص بك."],
                en: [
                    "This identity merges quiet archery with balanced duelling, letting your body behave like a precision instrument responding to the slightest cue. You move in spaces shaped like honour lanes, observing shoulders and feet as if conducting an orchestra.",
                    "You discover that your tools—be it bow, blade, or paddle—become extensions of thought. You learn to release motion without tension and celebrate every accurate strike as a personal signature."],
            },
            "why": {
                ar: [
                    "لأنك تفضل الإنجاز الصامت الذي يترك أثرًا عميقًا دون ضوضاء، وتؤمن بأن الأناقة الحركية جزء من هويتك. هذا المسار يتيح لك سكب ذكائك في كل ضربة بدقة غير متكلفة." ,
                    "تنتمي لهذا النمط لأنك توازن بين الحماس الداخلي والحضور الخارجي. تحب أن ترى النتيجة تظهر كوميض، لا كصراخ، وتشعر بالرضا حين يصفق قلبك قبل أي شخص آخر."],
                en: [
                    "Because you prefer quiet accomplishments leaving deep traces without noise and believe kinetic elegance defines you. This path lets you pour your intellect into each strike with effortless precision.",
                    "You belong here because you balance internal fire with composed presence. Seeing results appear as a flicker rather than a shout pleases you, and you relish the moment your heart applauds before anyone else."],
            },
            "real": {
                ar: [
                    "ستمر بجلسات تدريجية تبدأ بتمارين توازن وتنفس، ثم تنتقل إلى إطلاقات مركزة تُراجع بعدها تسجيلاتك أو ملاحظاتك. تتعلم قراءة أصابعك قبل الحركة، وضبط إيقاعك على نبض داخلي ثابت." ,
                    "قد يطلب منك أن تستبدل الأداة كل فترة كي تشعر بالفروق الدقيقة، أو أن تجرب المواجهة من زوايا متعددة. كل تجربة تعلّمك كيف تحافظ على أناقتك حتى عندما ترتفع حرارة المنافسة."],
                en: [
                    "You’ll progress through sessions starting with balance and breath work, then move to focused releases followed by reviewing footage or notes. You learn to read your fingers before movement and sync your tempo with a steady inner beat.",
                    "You may be asked to switch equipment occasionally to feel subtle differences or to duel from various angles. Each experience teaches you to keep elegance alive even when competition heats up."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nقف أمام مرآة وتخيل أنك تستعد لضربة حاسمة، ثم راقب كتفيك وراحة يديك. كرر التخيل مع تغيير بسيط في زاوية القدم أو زاوية الرأس، ولاحظ كيف يتغير الإحساس الداخلي. دوّن ما يمنحك شعور الاتزان." ,
                    "🔄 ابدأ من هنا\nاختر غرضًا بسيطًا في منزلك وتعامل معه كهدف دقيق: وجه نظرك نحوه، ثم حرر الحركة ببطء المخرجة التي تقود مشهدًا صامتًا. ركز على الشهيق والزفير قبل وبعد الحركة لتعرف كيف تستدعي الثقة وقت الحاجة."],
                en: [
                    "🔄 ابدأ من هنا\nStand before a mirror imagining a decisive strike, observing your shoulders and palms. Repeat the imagination while slightly altering foot or head angles, noticing how inner sensation changes. Record what gifts you that balanced feeling.",
                    "🔄 ابدأ من هنا\nPick a simple object at home and treat it as a precise target: direct your gaze, then release the move like a director guiding a silent scene. Track inhalation and exhalation before and after motion to learn how to summon confidence on demand."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nحافظ على طقوس صغيرة قبل كل حصة مثل ترتيب الأدوات أو لمس الأرض بأطراف أصابعك. إذا شعرت بأن الإيقاع أصبح ميكانيكيًا، استعن بسرد قصصي قصير لتعيد الحيوية وتسأل نفسك ماذا تعني هذه الضربة لشخصيتك." ,
                    "👁️‍🗨️ ملاحظات\nلا تقارن سرعتك بالآخرين؛ ركز على وضوح نيتك. احتفل بكل مرة تشعر فيها بأن الحركة خرجت كما تخيلتها، ولو كانت بسيطة. سجّل تلك اللحظات كي تبني أرشيفًا للثقة."],
                en: [
                    "👁️‍🗨️ ملاحظات\nKeep small rituals before each session—aligning equipment or grounding fingertips—to anchor your mind. If the rhythm turns mechanical, weave a short narrative to revive excitement and ask what the strike means to your character.",
                    "👁️‍🗨️ ملاحظات\nDo not compare your pace with others; focus on clarity of intent. Celebrate whenever a move unfolds exactly as imagined, even if it’s subtle, and archive those moments to build confidence."],
            },
        },
        "creative_teamplay": {
            "score": lambda ident: ident["social"] + 0.2 * ident["tactical"],
            "titles": {
                ar: ["Creative Teamplay", "مختبر الفريق الإبداعي"],
                en: ["Creative Teamplay", "Creative Team Lab"],
            },
            "silent": {
                ar: [
                    "{drivers}. تلتقط شرارة المجموعة بسرعة وتشعر أن الحوارات غير المنطوقة بينكم هي الوقود الحقيقي. تحب أن تراقب كيف تتدفق الأفكار من نظرة أو إيماءة لتتحول فورًا إلى حركة جماعية مليئة بالابتكار." ,
                    "{drivers}. ترى في الفريق لوحة فنية دائمة التغير، وكل عضو يضيف ضربته الخاصة. المحرك الصامت لديك هو تلك القدرة على دمج الأفكار بسرعة مع الحفاظ على متعة اللعب."],
                en: [
                    "{drivers}. You catch the team’s spark instantly and feel that unspoken dialogues are the true fuel. You enjoy watching ideas flow from a glance or gesture and transform into inventive group motion.",
                    "{drivers}. You see the team as an ever-changing art piece where each member adds a unique stroke. Your silent driver is the ability to merge ideas swiftly while preserving the delight of play."],
            },
            "what": {
                ar: [
                    "تشمل التجربة فوتسال تكتيكي، كرة سلة نصف ملعب، أو ألعابًا تعاونية تعتمد على إشارات سريعة وخطى مبتكرة. تمتد الفكرة إلى جلسات تبادل أدوار حيث يتحول اللاعبون إلى مخرجين للحظة، يبتكرون خدعًا عاطفية تبقي الملعب حيًا وتضيف طبقات من المرح." ,
                    "ستعيش في بيئة تشجع على السرد الجماعي؛ كل تمريرة تحمل قصة صغيرة وكل حركة مرتجلة تُستقبل بابتسامة. يتم تشجيعكم على تصميم مجموعات فنية، واستبدال المراكز الحركية في منتصف الجلسة، لتبقى الطاقة نابضة."],
                en: [
                    "Experiences include tactical futsal, half-court basketball, or cooperative games relying on quick signals and inventive steps. Role-switch sessions turn players into momentary directors crafting emotional feints that keep the court vibrant and playful.",
                    "You inhabit an environment that celebrates collective storytelling; every pass carries a tiny tale and every improvisation earns a smile. You are encouraged to choreograph artistic clusters and swap positions mid-session so the energy keeps humming."],
            },
            "why": {
                ar: [
                    "لأنك تؤمن بأن المتعة تنبع من التشارك، وترى أن الحوار الحركي أجمل من التعليمات الجامدة. تحتاج إلى مساحة تسمح لك بأن تكون قائدًا ومتلقيًا في اللحظة نفسها، وهذا المسار يمنحك ذلك بحرية." ,
                    "تحب أن تبني كيمياء حقيقية مع الآخرين، وتفرح حين ترى فكرة بسيطة تتحول إلى لعبة كاملة. هذا الأسلوب يجعلك شريكًا في صناعة الذكريات وليس مجرد متفرج."],
                en: [
                    "Because you believe joy springs from collaboration and kinetic dialogue beats rigid instructions. You need a space that lets you lead and receive simultaneously, and this path grants that freedom.",
                    "You adore forging real chemistry with others and rejoice when a simple idea evolves into a full game. This style turns you into a co-creator of memories rather than a spectator."],
            },
            "real": {
                ar: [
                    "في الواقع ستشارك في جلسات يتم فيها تبديل الأدوار بسرعة: مرة تكون صانع اللعب، ومرة تكون من يختتم المشهد. تُستخدم أدوات بسيطة مثل أشرطة ملونة أو بطاقات أفكار لضخ جرعات من الإبداع طوال الوقت." ,
                    "قد تدمجون بين مساحات داخلية وخارجية، وتبتكرون تحديات صغيرة تحفز الحوار بينكم. كل جلسة تنتهي بجلسة تقييم لطيفة حيث يشارك كل فرد شعوره الشخصي بدون حكم."],
                en: [
                    "In practice you join sessions where roles shift quickly—one moment you craft the play, the next you close the scene. Simple props like coloured bands or idea cards feed creativity throughout.",
                    "You may blend indoor and outdoor spots, designing mini challenges that spark conversation. Each session ends with a gentle debrief where everyone shares personal feelings without judgment."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nادعُ أصدقاءك لجلسة قصيرة تقسمون فيها الأدوار عشوائيًا، ثم اختر شخصًا واحدًا يقدّم فكرة مفاجئة. اتفقوا على رفع أيديكم كلما خطرت فكرة جديدة، ليصبح جسدكم لوحة إشارات مضيئة. في النهاية تحدثوا عن أكثر لحظة لمعت في قلوبكم." ,
                    "🔄 ابدأ من هنا\nحضّر بطاقة ملاحظات لكل فرد يكتب فيها شعورًا حركيًا يرغب في عيشه (مثل الدهشة أو الثقة). استخدموا هذه البطاقات كشرارة لبدء اللعب، وتذكروا أن تعطي كل شعور فرصته الكاملة قبل الانتقال لغيره."],
                en: [
                    "🔄 ابدأ من هنا\nInvite friends for a brief session where roles are assigned randomly, then pick one person to offer a surprise idea. Agree to raise your hands whenever a new spark arrives so your bodies become a board of luminous signals. Finish by sharing the moment that glowed in your hearts.",
                    "🔄 ابدأ من هنا\nPrepare note cards for each person to write a movement feeling they wish to live—wonder, trust, curiosity. Use these cards as sparks to kick off play and let every feeling enjoy its full spotlight before moving on."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nإذا لاحظت أن الأدوار أصبحت ثابتة، أعد خلطها في منتصف الجلسة. شجع الجميع على التعبير الأولي قبل التفكير الطويل، واحتفظ بأرشيف صغير للفكاها والمواقف المدهشة." ,
                    "👁️‍🗨️ ملاحظات\nاحترم حدود كل فرد واستمع لطاقته اليومية كي لا يتحول اللعب إلى ضغط. استمر في تدوير الأماكن والأساليب، فالبيئة الجديدة تمنح أفكارًا جديدة دائمًا."],
                en: [
                    "👁️‍🗨️ ملاحظات\nIf roles become fixed, reshuffle them mid-session. Encourage instant expression before overthinking and maintain a tiny archive of funny or striking moments.",
                    "👁️‍🗨️ ملاحظات\nRespect everyone’s boundaries and energy so play never becomes pressure. Keep rotating venues and styles because new environments spark fresh ideas."],
            },
        },
    }
    return data


ARCHETYPES = _archetype_data()


def _select_archetype_keys(identity: Dict[str, float], rng: random.Random) -> List[str]:
    scored = []
    for key, data in ARCHETYPES.items():
        score_func = data["score"]
        scored.append((score_func(identity) + rng.random() * 0.05, key))
    scored.sort(reverse=True)
    keys = [key for _, key in scored[:3]]
    if len(keys) < 3:
        for key in ARCHETYPES.keys():
            if key not in keys:
                keys.append(key)
            if len(keys) == 3:
                break
    return keys[:3]


def _compose_card(key: str, identity: Dict[str, float], drivers: List[str], lang: str, rng: random.Random) -> str:
    data = ARCHETYPES[key]
    locale = "ar" if lang in ("العربية", "ar") else "en"
    drivers_sentence = _drivers_sentence(drivers, lang)

    title = rng.choice(data["titles"][locale])
    silent_t = rng.choice(data["silent"][locale]).format(drivers=drivers_sentence)
    what_t = rng.choice(data["what"][locale])
    why_t = rng.choice(data["why"][locale])
    real_t = rng.choice(data["real"][locale])
    start_t = rng.choice(data["start"][locale])
    notes_t = rng.choice(data["notes"][locale])

    sections = [
        f"🎯 {title}",
        "",
        "💠 المحرك الصامت:",
        silent_t,
        "",
        "💡 ما هي؟",
        what_t,
        "",
        "🎮 ليه تناسبك؟",
        why_t,
        "",
        "🔍 شكلها الواقعي",
        real_t,
        "",
        start_t,
        "",
        notes_t,
    ]
    card = "\n".join(sections)
    return card


def _postprocess_text(text: str) -> str:
    cleaned = text
    for word in BANNED_TERMS:
        if word in cleaned:
            cleaned = cleaned.replace(word, "هوية ممتعة")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r" +", " ", cleaned)
    return cleaned.strip()


def _dedupe(cards: List[str], keys: List[str], identity: Dict[str, float], drivers: List[str], lang: str, rng: random.Random) -> List[str]:
    for _ in range(6):
        changed = False
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                if _jaccard(cards[i], cards[j]) >= 0.6:
                    cards[j] = _compose_card(keys[j], identity, drivers, lang, rng)
                    cards[j] = _postprocess_text(cards[j])
                    changed = True
        if not changed:
            break
    return cards



def _clean_json_payload(text: str) -> str:
    text = (text or '').strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?', '', text, flags=re.IGNORECASE).strip()
        if text.endswith('```'):
            text = text[:text.rfind('```')].strip()
    return text


def _parse_llm_response(raw: str) -> Optional[List[Dict[str, str]]]:
    if not raw:
        return None
    cleaned = _clean_json_payload(raw)
    data: Any
    try:
        data = json.loads(cleaned)
    except Exception:
        match = re.search(r'(\{.*\}|\[.*\])', cleaned, flags=re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(1))
        except Exception:
            return None
    if isinstance(data, dict):
        cards = data.get('cards') or data.get('recommendations')
    else:
        cards = data
    if not isinstance(cards, list):
        return None
    parsed: List[Dict[str, str]] = []
    for item in cards:
        if not isinstance(item, dict):
            continue
        lower = {str(k).lower(): str(v) for k, v in item.items()}
        title = lower.get('title') or lower.get('heading') or ''
        silent = lower.get('silent') or lower.get('silent_driver') or lower.get('identity') or ''
        what = lower.get('what') or lower.get('description') or ''
        why = lower.get('why') or lower.get('fit') or lower.get('reason') or ''
        real = lower.get('real') or lower.get('realistic') or lower.get('experience') or ''
        start = lower.get('start') or lower.get('start_here') or lower.get('launch') or ''
        notes = lower.get('notes') or lower.get('tips') or lower.get('remarks') or ''
        parts = [title, silent, what, why, real, start, notes]
        if all(p.strip() for p in parts):
            parsed.append({
                'title': title.strip(),
                'silent': silent.strip(),
                'what': what.strip(),
                'why': why.strip(),
                'real': real.strip(),
                'start': start.strip(),
                'notes': notes.strip(),
            })
    return parsed if len(parsed) >= 3 else None


def _format_llm_card(data: Dict[str, str], lang: str) -> str:
    title = data['title']
    silent = data['silent']
    what = data['what']
    why = data['why']
    real = data['real']
    start = data['start']
    notes = data['notes']
    sections = [
        f"🎯 {title}",
        '',
        '💠 المحرك الصامت:',
        silent,
        '',
        '💡 ما هي؟',
        what,
        '',
        '🎮 ليه تناسبك؟',
        why,
        '',
        '🔍 شكلها الواقعي',
        real,
        '',
        '🔄 ابدأ من هنا',
        start,
        '',
        '👁️‍🗨️ ملاحظات',
        notes,
    ]
    return '\n'.join(sections)


def _llm_cards(answers: Dict[str, Any], identity: Dict[str, float], drivers: List[str], lang: str) -> Optional[List[str]]:
    if chat_once is None or get_client_and_models is None:
        return None
    try:
        client, main_model, fallback_model = get_client_and_models()
    except Exception:
        client = None
        main_model = ''
        fallback_model = ''
    if not client or not main_model:
        return None

    driver_sentence = _drivers_sentence(drivers, lang)
    data = {
        'language': 'arabic' if lang in ('العربية', 'ar') else 'english',
        'identity_weights': identity,
        'drivers': drivers,
        'drivers_sentence': driver_sentence,
        'requirements': {
            'sections': [
                '🎯 العنوان', '💠 المحرك الصامت:', '💡 ما هي؟',
                '🎮 ليه تناسبك؟', '🔍 شكلها الواقعي', '🔄 ابدأ من هنا', '👁️‍🗨️ ملاحظات'
            ],
            'min_words_per_card': 120,
            'banned_terms': BANNED_TERMS,
            'tone': 'identity-focused, joyful, no schedules or numeric time commitments'
        }
    }

    system_prompt = (
        "أنت مساعد SportSync. اكتب ثلاث بطاقات توصية رياضية عربية فصيحة بإحساس إنساني غني."
        " احرص على استخدام الأقسام بالتسلسل التالي: 🎯 العنوان، 💠 المحرك الصامت:, 💡 ما هي؟, 🎮 ليه تناسبك؟, 🔍 شكلها الواقعي, 🔄 ابدأ من هنا, 👁️‍🗨️ ملاحظات."
        " تجنب أي حديث عن الأوقات أو العدّ أو السعرات أو الوزن. أعد الاستجابة بصيغة JSON تحتوي على المفتاح cards وقيمته قائمة من ثلاثة كائنات تضم الحقول title, silent, what, why, real, start, notes."
    ) if lang in ('العربية', 'ar') else (
        "You are the SportSync assistant. Write three expressive sport-identity cards in English."
        " Use exactly these sections in order: 🎯 العنوان, 💠 المحرك الصامت:, 💡 ما هي؟, 🎮 ليه تناسبك؟, 🔍 شكلها الواقعي, 🔄 ابدأ من هنا, 👁️‍🗨️ ملاحظات."
        " Avoid mentioning explicit durations, repetition counts, calories, or weight loss. Respond as JSON with a 'cards' array containing objects with fields title, silent, what, why, real, start, notes."
    )

    user_prompt = json.dumps(data, ensure_ascii=False)

    model_chain = main_model
    try:
        from core.llm_client import _split_models_csv as _split  # type: ignore
    except Exception:
        _split = None
    if fallback_model and _split:
        models_list = _split(main_model)
        if fallback_model not in models_list:
            model_chain = ",".join(models_list + [fallback_model]) if models_list else fallback_model
    try:
        raw = chat_once(
            client,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model_chain or main_model,
            temperature=0.65,
            max_tokens=2200,
            top_p=0.9,
        )
    except Exception:
        return None

    parsed = _parse_llm_response(raw)
    if not parsed:
        return None

    cards: List[str] = []
    for item in parsed[:3]:
        card_text = _format_llm_card(item, lang)
        card_text = _postprocess_text(card_text)
        if len(card_text.split()) < 120:
            return None
        cards.append(card_text)
    return cards

def _generate_cards(answers: Dict[str, Any], lang: str) -> List[str]:
    session_id = _session_id_from_answers(answers)
    seed_base = session_id + _stable_json(answers) + datetime.utcnow().strftime("%Y-%m-%d")
    seed = int(hashlib.sha256(seed_base.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)

    identity = _extract_identity(answers)
    drivers = _drivers(identity, lang)
    keys = _select_archetype_keys(identity, rng)

    cards = []
    for key in keys:
        card = _compose_card(key, identity, drivers, lang, rng)
        card = _postprocess_text(card)
        cards.append(card)

    cards = _dedupe(cards, keys, identity, drivers, lang, rng)

    final_cards = []
    for card in cards:
        if len(card.split()) < 120:
            extra = "\n" + ("هذه البطاقة تدعوك للاستماع لفضولك الداخلي وتذكرك بأن المتعة أصدق دليل." if lang in ("العربية", "ar") else "This card invites you to listen to inner curiosity and reminds you that delight is the truest compass.")
            card += extra
        if len(card) < 600:
            filler = "\n" + ("اسمح للكلمات أن تتحول إلى صور، وللصور أن تتحول إلى حركات تعبر عنك بلا توتر." if lang in ("العربية", "ar") else "Let words turn into imagery and let imagery become movement that expresses you without strain.")
            card += filler
        final_cards.append(_postprocess_text(card))
    return final_cards


def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
    """
    يُرجع List[str] من 3 بطاقات Recommendation طويلة بصيغة موحّدة.
    - صيغة كل بطاقة:
      🎯 العنوان
      💠 المحرك الصامت:
      💡 ما هي؟
      🎮 ليه تناسبك؟
      🔍 شكلها الواقعي
      🔄 ابدأ من هنا
      👁️‍🗨️ ملاحظات
    - تمنع التشابه العالي بين البطاقات.
    - تستخدم seed حتمي من (session_id + تجزئة الإجابات + تاريخ اليوم) للتنوع عبر الجلسات.
    - تتجنب كلمات “خسارة الوزن/حرق الدهون” وتستبدلها بهوية ومتعة.
    """
    global LAST_RECOMMENDER_SOURCE

    answers_copy: Dict[str, Any] = dict(answers or {})
    force_flag = bool(answers_copy.pop("_force_fallback", False))
    env_force = os.getenv("FORCE_ANALYTICAL_FALLBACK", "").strip().lower() == "true"
    disable_flag = os.getenv("DISABLE_LLM", "").strip().lower() == "true"
    session_id = _session_id_from_answers(answers_copy)

    identity = _extract_identity(answers_copy)
    drivers = _drivers(identity, lang)

    cards: Optional[List[str]] = None
    source = "fallback"

    if not (force_flag or env_force or disable_flag):
        try:
            cards = _llm_cards(answers_copy, identity, drivers, lang)
            if cards:
                source = "llm"
        except Exception:
            cards = None

    if not cards:
        cards = _generate_cards(answers_copy, lang)
        source = "fallback"

    LAST_RECOMMENDER_SOURCE = source

    try:
        log_event(
            user_id=str(answers_copy.get("_user_id", "unknown")),
            session_id=session_id,
            name="generate_recommendation",
            payload={"source": source},
            lang=lang,
        )
    except Exception:
        pass

    return cards


def get_last_rec_source() -> str:
    return LAST_RECOMMENDER_SOURCE


if __name__ == "__main__":
    sample_answers = {"q1": {"answer": ["أحب الذكاء والتخطيط"]}, "_session_id": "demo-session"}
    recs = generate_sport_recommendation(sample_answers, "العربية")
    assert len(recs) == 3
    assert all(len(r) > 600 for r in recs)
    print("OK", [len(r) for r in recs])
