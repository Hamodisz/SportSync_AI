# خطة إصلاح المشاكل الثلاث في SportSync_AI

## 📋 ملخص المشاكل

### ✅ 1. Import Error - تم حلها!
**المشكلة:** `log_user_insight` مو موجودة في `user_logger.py`
**الحل:** ✅ تمت إضافتها

### 🔴 2. الصياغة غير البشرية
**المشكلة:** النظام يستخدم `FALLBACK_BLUEPRINTS` المشفرة بدلاً من الملفات الحقيقية
**الموقع:** `core/backend_gpt.py` خطوط 1402-1530

### 🔴 3. الصور والفيديو ما تطلع (RunPod)
**المشكلة:** الإعدادات ما مضبوطة بشكل صحيح
**الموقع:** ملف `.env` و `content_studio/`

---

## 🛠️ خطة العمل التفصيلية

### المرحلة 1: إصلاح نظام التوصيات

#### الخطوة 1: تعديل `backend_gpt.py` لاستخدام KB Ranker

**الملف:** `core/backend_gpt.py`
**الموقع:** دالة `_generate_cards` (سطر 1402)

**التعديل المطلوب:**
```python
def _generate_cards(
    answers: Dict[str, Any],
    lang: str,
    *,
    identity: Optional[Dict[str, float]] = None,
    drivers: Optional[List[str]] = None,
    traits: Optional[Dict[str, float]] = None,
    rng: Optional[random.Random] = None,
) -> List[Dict[str, Any]]:
    """
    استخدام KB Ranker بدلاً من FALLBACK_BLUEPRINTS
    """
    from pathlib import Path
    import core.kb_ranker as kb_ranker
    
    # المسارات
    kb_path = Path("data/sportsync_knowledge.json")
    identities_dir = Path("data/identities")
    
    # استخدام KB Ranker للحصول على البطاقات الصحيحة
    try:
        cards_text = kb_ranker.rank_and_render(
            answers=answers,
            lang=lang,
            kb_path=kb_path,
            identities_dir=identities_dir,
            top_k=3
        )
        
        # تحويل النص إلى هيكل البطاقات
        cards = []
        for card_text in cards_text:
            if card_text == "—":
                continue
            # تحويل النص إلى dict
            card_dict = _parse_kb_card_to_dict(card_text, lang)
            cards.append(card_dict)
        
        # لو ما كفت، نستخدم fallback
        while len(cards) < 3:
            session_id = _session_id_from_answers(answers)
            seed_base = session_id + _stable_json(answers) + datetime.utcnow().strftime("%Y-%m-%d")
            local_rng = rng or random.Random(int(hashlib.sha256(seed_base.encode("utf-8")).hexdigest(), 16))
            
            identity = identity or _extract_identity(answers)
            drivers = drivers or _drivers(identity, lang)
            traits = traits or _derive_binary_traits(answers)
            
            blueprint_order = _egate_fallback(identity, traits, local_rng)
            cards.append(_fallback_identity(blueprint_order[len(cards)], lang, identity, traits, drivers, local_rng))
        
        return cards[:3]
        
    except Exception as e:
        print(f"[ERROR] KB Ranker failed: {e}, falling back to blueprints")
        # استخدام الكود القديم كـ fallback نهائي
        session_id = _session_id_from_answers(answers)
        seed_base = session_id + _stable_json(answers) + datetime.utcnow().strftime("%Y-%m-%d")
        local_rng = rng or random.Random(int(hashlib.sha256(seed_base.encode("utf-8")).hexdigest(), 16))

        identity = identity or _extract_identity(answers)
        drivers = drivers or _drivers(identity, lang)
        traits = traits or _derive_binary_traits(answers)

        blueprint_order = _egate_fallback(identity, traits, local_rng)
        primary_cards = []
        for blueprint in blueprint_order[:3]:
            primary_cards.append(_fallback_identity(blueprint, lang, identity, traits, drivers, local_rng))

        cards = _hard_dedupe_and_fill(primary_cards, blueprint_order, lang, identity, traits, drivers, local_rng)
        return cards
```

#### الخطوة 2: إضافة دالة المساعدة

**إضافة في نفس الملف:**
```python
def _parse_kb_card_to_dict(card_text: str, lang: str) -> Dict[str, Any]:
    """
    تحويل نص البطاقة من KB Ranker إلى dict
    """
    lines = card_text.split('\n')
    card = {
        'sport_label': '',
        'what_it_looks_like': [],
        'why_you': [],
        'real_world': [],
        'notes': []
    }
    
    current_section = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if '🎯' in line and ('الهوية المثالية' in line or 'Ideal identity' in line):
            card['sport_label'] = line.split(':')[-1].strip()
        elif '💡' in line:
            current_section = 'what'
        elif '🎮' in line or 'لماذا' in line or 'Why' in line:
            current_section = 'why'
        elif '⚙️' in line or 'كيف تبدأ' in line or 'How To Begin' in line or 'First week' in line:
            current_section = 'start'
        elif '🧠' in line or '👁‍🗨' in line:
            current_section = 'notes'
        elif line.startswith('-'):
            text = line[1:].strip()
            if current_section == 'what':
                card['what_it_looks_like'].append(text)
            elif current_section == 'why':
                card['why_you'].append(text)
            elif current_section == 'start':
                card['real_world'].append(text)
            elif current_section == 'notes':
                card['notes'].append(text)
    
    return card
```

---

### المرحلة 2: إصلاح RunPod للصور والفيديو

#### الخطوة 1: التحقق من الإعدادات

**الملف:** `.env`
**تأكد من:**
```bash
# RunPod Settings
RUNPOD_API_KEY=your-actual-api-key-here
RUNPOD_COMFY_ENDPOINT_ID=your-actual-endpoint-id

# Image Generation
USE_RUNPOD_IMAGES=1
USE_IMAGE_PLACEHOLDERS=0
```

#### الخطوة 2: فحص content_studio

**الملف:** `content_studio/ai_images/` و `content_studio/ai_video/`

تأكد من:
1. الملفات تستدعي `runpod_client.py` بشكل صحيح
2. معالجة الأخطاء موجودة
3. الـ fallback يعمل لو فشل RunPod

---

## 📝 الأوامر المطلوبة

### 1. تطبيق التعديلات
```bash
# النسخ الاحتياطي أولاً
cp core/backend_gpt.py core/backend_gpt.py.backup

# تطبيق التعديلات (سأقوم بها)
```

### 2. اختبار النظام
```bash
# تشغيل الاختبارات
python -m pytest tests/test_reco_pipeline.py -v

# اختبار يدوي
python core/backend_gpt.py
```

### 3. التحقق من RunPod
```bash
# اختبار RunPod API
python scripts/test_runpod.py
python scripts/test_runpod_flux.py
```

---

## ✅ قائمة التحقق النهائية

### قبل النشر:
- [ ] تم إضافة `log_user_insight` في `user_logger.py` ✅
- [ ] تم تعديل `_generate_cards` لاستخدام KB Ranker
- [ ] تم إضافة `_parse_kb_card_to_dict`
- [ ] تم اختبار التوصيات يدوياً
- [ ] تم التحقق من RunPod API keys
- [ ] تم اختبار توليد الصور
- [ ] تم اختبار توليد الفيديو

### بعد النشر:
- [ ] مراقبة اللوقات للتأكد من عدم وجود أخطاء
- [ ] التحقق من جودة التوصيات
- [ ] التحقق من عمل الصور والفيديو

---

## 🚨 ملاحظات مهمة

1. **النسخ الاحتياطي:** دائماً اعمل backup قبل التعديل
2. **الاختبار:** اختبر كل تعديل على حدة
3. **المراقبة:** راقب اللوقات بعد النشر
4. **الـ Fallback:** تأكد إن الـ fallback يشتغل لو فشل أي شيء

---

## 📞 الخطوات التالية

1. أراجع معك التعديلات المقترحة
2. نطبق التعديلات خطوة بخطوة
3. نختبر النظام
4. ننشر على production

هل تبي نبدأ التطبيق الحين؟
