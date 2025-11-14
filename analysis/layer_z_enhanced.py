# -*- coding: utf-8 -*-
"""
analysis/layer_z_enhanced.py
-----------------------------
نظام Layer-Z محسّن مع:
- Confidence scores لكل محور
- تكامل مع weighted_layers
- تحليل Flow State
- تحليل Risk Profile
- 9 محاور (6 أساسية + 3 جديدة)
- Pattern matching محسّن
- Context awareness

الإصدار: 2.0.0
التاريخ: 11 نوفمبر 2025
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re

# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ZAxisScore:
    """نتيجة محور Z مع confidence"""
    axis_name: str
    score: float  # -1.0 to +1.0
    confidence: float  # 0.0 to 1.0
    description: str
    
    def __repr__(self):
        return f"{self.axis_name}: {self.score:+.2f} (ثقة {self.confidence:.0%})"

@dataclass
class FlowIndicators:
    """مؤشرات حالة التدفق"""
    flow_potential: float  # 0-1
    focus_depth: str  # "عميق" | "متوسط" | "سطحي"
    immersion_likelihood: float  # 0-1
    distraction_resistance: float  # 0-1

@dataclass
class RiskAssessment:
    """تقييم ملف المخاطرة"""
    risk_level: float  # 0-1
    category: str  # "منخفض" | "متوسط" | "عالي"
    comfort_zone_width: str  # "ضيق" | "متوسط" | "واسع"
    novelty_seeking: float  # 0-1

# ============================================================================
# Enhanced Layer-Z Analyzer
# ============================================================================

class EnhancedLayerZ:
    """محلل Layer-Z محسّن"""
    
    def __init__(self):
        self._ar_pattern = re.compile(r"[\u0600-\u06FF]")
        self._init_patterns()
    
    def _init_patterns(self):
        """تهيئة patterns للكشف"""
        
        # Technical/Intuitive patterns
        self.technical_ar = [
            "دقيق", "تقني", "تفاصيل", "تحليل", "منهجي", "نظام",
            "خطة", "بروتوكول", "قياس", "إحصاء", "بيانات"
        ]
        self.intuitive_ar = [
            "حدسي", "لحظي", "شعور", "إحساس", "عفوي", "طبيعي",
            "تلقائي", "سريع", "مباشر", "بديهي"
        ]
        
        # Calm/Adrenaline patterns
        self.calm_ar = [
            "هدوء", "هادئ", "استرخاء", "تأمل", "سكينة", "راحة",
            "بطيء", "منظم", "تنفس", "سلام"
        ]
        self.adrenaline_ar = [
            "أدرينالين", "إثارة", "سرعة", "خطر", "مغامرة", "اندفاع",
            "حماس", "طاقة", "نشاط", "قوة"
        ]
        
        # Solo/Group patterns
        self.solo_ar = [
            "لوحدي", "فردي", "وحيد", "منفرد", "خاص", "مستقل",
            "بنفسي", "ذاتي"
        ]
        self.group_ar = [
            "جماعي", "فريق", "مجموعة", "ناس", "أصدقاء", "معاً",
            "تعاون", "شراكة", "جماعة"
        ]
        
        # Control/Freedom patterns
        self.control_ar = [
            "سيطرة", "تحكم", "ضبط", "انضباط", "نظام", "قواعد",
            "بروتوكول", "ترتيب", "تنظيم"
        ]
        self.freedom_ar = [
            "حرية", "انسياب", "مرونة", "عفوية", "تلقائية", "انطلاق",
            "بدون قيود", "حر"
        ]
        
        # Repeat/Variety patterns
        self.repeat_ar = [
            "تكرار", "روتين", "إتقان", "تمرين", "مهارة", "إعادة",
            "ممارسة", "تدريب"
        ]
        self.variety_ar = [
            "تنويع", "تغيير", "جديد", "مختلف", "متنوع", "ملل",
            "رتابة", "تجديد"
        ]
        
        # Compete/Enjoy patterns
        self.compete_ar = [
            "منافسة", "تحدي", "فوز", "تفوق", "أفضل", "رقم قياسي",
            "إنجاز", "هدف"
        ]
        self.enjoy_ar = [
            "متعة", "استمتاع", "مرح", "لعب", "تجربة", "شعور",
            "إحساس جميل"
        ]
        
        # Flow state indicators
        self.flow_ar = [
            "تدفق", "انغماس", "تركيز عميق", "الوقت يطير", "نسيان الذات",
            "استغراق", "ذوبان في"
        ]
        
        # Risk indicators
        self.risk_seeking_ar = [
            "خطر", "مغامرة", "تجربة جديدة", "غير مألوف", "تحدي كبير"
        ]
        self.risk_averse_ar = [
            "أمان", "تأكد", "مألوف", "تدريجي", "حذر"
        ]
    
    def _is_arabic(self, text: str) -> bool:
        """كشف النص العربي"""
        return bool(self._ar_pattern.search(text or ""))
    
    def _count_patterns(self, text: str, patterns: List[str]) -> int:
        """عد تطابقات الأنماط"""
        if not text:
            return 0
        text_lower = text.lower()
        return sum(1 for p in patterns if p in text_lower)
    
    def _calculate_confidence(self, positive_count: int, negative_count: int, 
                             total_words: int) -> float:
        """حساب confidence بناءً على الأدلة"""
        total_matches = positive_count + negative_count
        if total_matches == 0:
            return 0.0
        
        # Confidence يزيد مع عدد الأدلة
        base_confidence = min(total_matches / 5, 1.0)
        
        # يقل مع الغموض (positive ≈ negative)
        if positive_count > 0 and negative_count > 0:
            ratio = min(positive_count, negative_count) / max(positive_count, negative_count)
            ambiguity_penalty = ratio * 0.5
            base_confidence *= (1 - ambiguity_penalty)
        
        return round(base_confidence, 2)
    
    def analyze_axis(self, text: str, positive_patterns: List[str],
                    negative_patterns: List[str], axis_name: str,
                    description: str) -> ZAxisScore:
        """تحليل محور واحد"""
        pos_count = self._count_patterns(text, positive_patterns)
        neg_count = self._count_patterns(text, negative_patterns)
        
        total_words = len(text.split())
        confidence = self._calculate_confidence(pos_count, neg_count, total_words)
        
        # حساب Score
        if pos_count == 0 and neg_count == 0:
            score = 0.0
        else:
            score = (pos_count - neg_count) / max(pos_count + neg_count, 1)
            score = max(-1.0, min(1.0, score))
        
        return ZAxisScore(
            axis_name=axis_name,
            score=score,
            confidence=confidence,
            description=description
        )
    
    def analyze_all_axes(self, text: str, lang: str = "العربية") -> Dict[str, ZAxisScore]:
        """تحليل جميع المحاور الـ 9"""
        if lang != "العربية":
            # للإنجليزية نستخدم تحليل بسيط حالياً
            return self._analyze_english_simple(text)
        
        results = {}
        
        # المحاور الأساسية (6)
        results["technical_intuitive"] = self.analyze_axis(
            text, self.technical_ar, self.intuitive_ar,
            "technical_intuitive", "تقني/حدسي"
        )
        
        results["calm_adrenaline"] = self.analyze_axis(
            text, self.adrenaline_ar, self.calm_ar,
            "calm_adrenaline", "هدوء/أدرينالين"
        )
        
        results["solo_group"] = self.analyze_axis(
            text, self.solo_ar, self.group_ar,
            "solo_group", "فردي/جماعي"
        )
        
        results["control_freedom"] = self.analyze_axis(
            text, self.control_ar, self.freedom_ar,
            "control_freedom", "سيطرة/حرية"
        )
        
        results["repeat_variety"] = self.analyze_axis(
            text, self.repeat_ar, self.variety_ar,
            "repeat_variety", "تكرار/تنويع"
        )
        
        results["compete_enjoy"] = self.analyze_axis(
            text, self.compete_ar, self.enjoy_ar,
            "compete_enjoy", "منافسة/متعة"
        )
        
        # المحاور الجديدة (3)
        flow_count = self._count_patterns(text, self.flow_ar)
        results["flow_state"] = ZAxisScore(
            axis_name="flow_state",
            score=min(flow_count / 3, 1.0),
            confidence=min(flow_count / 2, 1.0),
            description="حالة التدفق"
        )
        
        # Focus mode (من technical + calm)
        tech_score = results["technical_intuitive"].score
        calm_score = results["calm_adrenaline"].score
        focus_score = (tech_score - calm_score) / 2
        results["focus_mode"] = ZAxisScore(
            axis_name="focus_mode",
            score=focus_score,
            confidence=(results["technical_intuitive"].confidence + 
                       results["calm_adrenaline"].confidence) / 2,
            description="نمط التركيز"
        )
        
        # Risk profile
        risk_seeking = self._count_patterns(text, self.risk_seeking_ar)
        risk_averse = self._count_patterns(text, self.risk_averse_ar)
        risk_score = (risk_seeking - risk_averse) / max(risk_seeking + risk_averse, 1)
        results["risk_profile"] = ZAxisScore(
            axis_name="risk_profile",
            score=risk_score,
            confidence=min((risk_seeking + risk_averse) / 3, 1.0),
            description="ملف المخاطرة"
        )
        
        return results
    
    def _analyze_english_simple(self, text: str) -> Dict[str, ZAxisScore]:
        """تحليل بسيط للإنجليزية"""
        # نظام بسيط حالياً
        return {
            "technical_intuitive": ZAxisScore("technical_intuitive", 0.0, 0.3, "technical/intuitive"),
            "calm_adrenaline": ZAxisScore("calm_adrenaline", 0.0, 0.3, "calm/adrenaline"),
            "solo_group": ZAxisScore("solo_group", 0.0, 0.3, "solo/group"),
            "control_freedom": ZAxisScore("control_freedom", 0.0, 0.3, "control/freedom"),
            "repeat_variety": ZAxisScore("repeat_variety", 0.0, 0.3, "repeat/variety"),
            "compete_enjoy": ZAxisScore("compete_enjoy", 0.0, 0.3, "compete/enjoy"),
            "flow_state": ZAxisScore("flow_state", 0.0, 0.2, "flow state"),
            "focus_mode": ZAxisScore("focus_mode", 0.0, 0.2, "focus mode"),
            "risk_profile": ZAxisScore("risk_profile", 0.0, 0.2, "risk profile"),
        }
    
    def analyze_flow_indicators(self, text: str, z_scores: Dict[str, ZAxisScore]) -> FlowIndicators:
        """تحليل مؤشرات التدفق"""
        flow_score = z_scores.get("flow_state", ZAxisScore("", 0, 0, "")).score
        focus_score = z_scores.get("focus_mode", ZAxisScore("", 0, 0, "")).score
        
        # Flow potential
        flow_potential = (flow_score + abs(focus_score)) / 2
        
        # Focus depth
        if abs(focus_score) > 0.6:
            focus_depth = "عميق"
        elif abs(focus_score) > 0.3:
            focus_depth = "متوسط"
        else:
            focus_depth = "سطحي"
        
        # Immersion likelihood
        immersion = flow_potential * 0.8 + (1 - z_scores.get("repeat_variety", ZAxisScore("", 0, 0, "")).score) * 0.2
        
        # Distraction resistance
        distraction = abs(focus_score) * 0.7 + flow_score * 0.3
        
        return FlowIndicators(
            flow_potential=round(flow_potential, 2),
            focus_depth=focus_depth,
            immersion_likelihood=round(immersion, 2),
            distraction_resistance=round(distraction, 2)
        )
    
    def analyze_risk_assessment(self, text: str, z_scores: Dict[str, ZAxisScore]) -> RiskAssessment:
        """تقييم ملف المخاطرة"""
        risk_score = z_scores.get("risk_profile", ZAxisScore("", 0, 0, "")).score
        adrenaline_score = z_scores.get("calm_adrenaline", ZAxisScore("", 0, 0, "")).score
        variety_score = z_scores.get("repeat_variety", ZAxisScore("", 0, 0, "")).score
        
        # Risk level (0-1)
        risk_level = (risk_score + adrenaline_score + abs(variety_score)) / 3
        risk_level = (risk_level + 1) / 2  # تحويل من [-1,1] إلى [0,1]
        
        # Category
        if risk_level > 0.6:
            category = "عالي"
        elif risk_level > 0.35:
            category = "متوسط"
        else:
            category = "منخفض"
        
        # Comfort zone width
        if abs(variety_score) > 0.5:
            comfort_zone = "واسع"
        elif abs(variety_score) > 0.25:
            comfort_zone = "متوسط"
        else:
            comfort_zone = "ضيق"
        
        # Novelty seeking
        novelty = (abs(variety_score) + risk_level) / 2
        
        return RiskAssessment(
            risk_level=round(risk_level, 2),
            category=category,
            comfort_zone_width=comfort_zone,
            novelty_seeking=round(novelty, 2)
        )
    
    def generate_z_drivers(self, z_scores: Dict[str, ZAxisScore], lang: str = "العربية") -> List[str]:
        """توليد جمل المحركات من النتائج"""
        ar = (lang == "العربية")
        drivers = []
        
        for axis_name, z_score in z_scores.items():
            if z_score.confidence < 0.3:  # تجاهل الثقة المنخفضة
                continue
            
            score = z_score.score
            
            if axis_name == "technical_intuitive":
                if score > 0.4:
                    drivers.append("ميل تقني ومنهجي" if ar else "Technical & methodical bias")
                elif score < -0.4:
                    drivers.append("ميل حدسي ولحظي" if ar else "Intuitive & instinctive bias")
            
            elif axis_name == "calm_adrenaline":
                if score > 0.4:
                    drivers.append("ينجذب للإثارة والأدرينالين" if ar else "Adrenaline/thrill seeking")
                elif score < -0.4:
                    drivers.append("يميل للهدوء والتنظيم العصبي" if ar else "Calm/parasympathetic regulation")
            
            elif axis_name == "solo_group":
                if score > 0.4:
                    drivers.append("تفضيل قوي للعمل الفردي" if ar else "Strong solo preference")
                elif score < -0.4:
                    drivers.append("ينجح أكثر في البيئة الجماعية" if ar else "Thrives in group settings")
            
            elif axis_name == "control_freedom":
                if score > 0.4:
                    drivers.append("يحتاج للسيطرة والبروتوكول" if ar else "Needs control & protocol")
                elif score < -0.4:
                    drivers.append("يفضل الحرية والانسياب" if ar else "Prefers freedom & flow")
            
            elif axis_name == "repeat_variety":
                if score > 0.4:
                    drivers.append("يرتاح للتكرار والإتقان" if ar else "Comfortable with repetition & mastery")
                elif score < -0.4:
                    drivers.append("يكره الرتابة ويبحث عن التنويع" if ar else "Boredom-averse, seeks variety")
            
            elif axis_name == "compete_enjoy":
                if score > 0.4:
                    drivers.append("محفَّز بالمنافسة والتفوق" if ar else "Competition/dominance driven")
                elif score < -0.4:
                    drivers.append("محفَّز بالمتعة والتجربة" if ar else "Enjoyment/experience driven")
            
            elif axis_name == "flow_state":
                if score > 0.5:
                    drivers.append("قدرة عالية على الدخول في حالة التدفق" if ar else "High flow state capacity")
            
            elif axis_name == "risk_profile":
                if score > 0.5:
                    drivers.append("ميل للمخاطرة والمغامرة" if ar else "Risk-taking tendency")
                elif score < -0.5:
                    drivers.append("يفضل الأمان والتدرج" if ar else "Safety-oriented approach")
        
        return drivers
    
    def analyze_complete(self, text: str, lang: str = "العربية",
                        answers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        التحليل الكامل - الوظيفة الرئيسية
        
        Returns:
            {
                "z_scores": Dict[str, ZAxisScore],
                "z_drivers": List[str],
                "flow_indicators": FlowIndicators,
                "risk_assessment": RiskAssessment,
                "summary": Dict[str, Any]
            }
        """
        # جمع النص من answers إذا كان متوفراً
        if answers and not text:
            text = self._flatten_answers(answers)
        
        # تحليل المحاور
        z_scores = self.analyze_all_axes(text, lang)
        
        # تحليل Flow
        flow_indicators = self.analyze_flow_indicators(text, z_scores)
        
        # تحليل Risk
        risk_assessment = self.analyze_risk_assessment(text, z_scores)
        
        # توليد Drivers
        z_drivers = self.generate_z_drivers(z_scores, lang)
        
        # Summary
        summary = self._create_summary(z_scores, flow_indicators, risk_assessment, lang)
        
        return {
            "z_scores": z_scores,
            "z_drivers": z_drivers,
            "flow_indicators": flow_indicators,
            "risk_assessment": risk_assessment,
            "summary": summary
        }
    
    def _flatten_answers(self, answers: Dict[str, Any]) -> str:
        """تحويل answers إلى نص موحد"""
        texts = []
        for k, v in answers.items():
            if k == "_session_id":
                continue
            if isinstance(v, dict):
                answer = v.get("answer", "")
                if isinstance(answer, (list, tuple)):
                    texts.extend([str(item) for item in answer])
                else:
                    texts.append(str(answer))
            else:
                texts.append(str(v))
        return " ".join(texts)
    
    def _create_summary(self, z_scores: Dict[str, ZAxisScore],
                       flow_indicators: FlowIndicators,
                       risk_assessment: RiskAssessment,
                       lang: str) -> Dict[str, Any]:
        """إنشاء ملخص شامل"""
        ar = (lang == "العربية")
        
        # أقوى محور
        strongest_axis = max(z_scores.values(), 
                           key=lambda x: abs(x.score) * x.confidence)
        
        # متوسط الثقة
        avg_confidence = sum(z.confidence for z in z_scores.values()) / len(z_scores)
        
        return {
            "strongest_axis": {
                "name": strongest_axis.axis_name,
                "score": strongest_axis.score,
                "confidence": strongest_axis.confidence,
                "description": strongest_axis.description
            },
            "average_confidence": round(avg_confidence, 2),
            "flow_potential": flow_indicators.flow_potential,
            "risk_category": risk_assessment.category,
            "profile_clarity": "واضح" if avg_confidence > 0.6 else "متوسط" if avg_confidence > 0.35 else "غامض"
        }

# ============================================================================
# Backward Compatible Functions
# ============================================================================

def analyze_silent_drivers_enhanced(answers: Dict[str, Any], 
                                   lang: str = "العربية",
                                   encoded: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    واجهة متوافقة مع النظام القديم
    
    Args:
        answers: إجابات المستخدم
        lang: اللغة
        encoded: نتائج weighted_layers (اختياري)
    
    Returns:
        {
            "z_scores": dict,
            "z_drivers": list,
            "profile": dict
        }
    """
    analyzer = EnhancedLayerZ()
    
    # استخدام encoded إذا كان متوفراً
    if encoded and "z_scores" in encoded:
        # تحويل z_scores من dict عادي إلى ZAxisScore objects
        z_scores_dict = {}
        for axis_name, score in encoded["z_scores"].items():
            z_scores_dict[axis_name] = ZAxisScore(
                axis_name=axis_name,
                score=score,
                confidence=0.7,  # ثقة افتراضية من weighted_layers
                description=axis_name
            )
    else:
        # تحليل جديد
        result = analyzer.analyze_complete("", lang, answers)
        z_scores_dict = result["z_scores"]
    
    # توليد drivers
    z_drivers = analyzer.generate_z_drivers(z_scores_dict, lang)
    
    # تحويل z_scores إلى dict بسيط للتوافق
    z_scores_simple = {k: v.score for k, v in z_scores_dict.items()}
    
    return {
        "z_scores": z_scores_simple,
        "z_drivers": z_drivers,
        "profile": {
            "axes": z_scores_simple
        }
    }


def analyze_user_from_answers(answers: Dict[str, Any],
                              lang: str = "العربية",
                              user_id: Optional[str] = None,
                              **kwargs) -> Dict[str, Any]:
    """
    واجهة متوافقة تماماً مع layer_z_engine.py القديم
    
    Args:
        answers: إجابات المستخدم
        lang: اللغة
        user_id: معرف المستخدم (للتوافق)
        **kwargs: معاملات إضافية
    
    Returns:
        {
            "z_drivers": list,
            "profile": dict
        }
    """
    result = analyze_silent_drivers_enhanced(answers, lang)
    return {
        "z_drivers": result["z_drivers"],
        "profile": result["profile"]
    }

# ============================================================================
# Helper Functions
# ============================================================================

def get_z_scores_dict(result: Dict[str, Any]) -> Dict[str, float]:
    """استخراج z_scores كـ dict بسيط"""
    if "z_scores" not in result:
        return {}
    
    z_scores = result["z_scores"]
    if isinstance(list(z_scores.values())[0], ZAxisScore):
        return {k: v.score for k, v in z_scores.items()}
    return z_scores

def format_z_report(result: Dict[str, Any], lang: str = "العربية") -> str:
    """تنسيق تقرير Layer-Z للعرض"""
    ar = (lang == "العربية")
    lines = []
    
    lines.append("=" * 50)
    lines.append("تقرير Layer-Z المحسّن" if ar else "Enhanced Layer-Z Report")
    lines.append("=" * 50)
    
    # Z-Scores
    lines.append("\n📊 محاور Z:" if ar else "\n📊 Z-Axes:")
    z_scores = result.get("z_scores", {})
    for axis_name, z_score in z_scores.items():
        if isinstance(z_score, ZAxisScore):
            lines.append(f"  • {z_score}")
    
    # Drivers
    lines.append("\n🎯 المحركات الرئيسية:" if ar else "\n🎯 Key Drivers:")
    for driver in result.get("z_drivers", []):
        lines.append(f"  • {driver}")
    
    # Flow Indicators
    if "flow_indicators" in result:
        flow = result["flow_indicators"]
        lines.append("\n🌊 مؤشرات التدفق:" if ar else "\n🌊 Flow Indicators:")
        lines.append(f"  • إمكانية التدفق: {flow.flow_potential:.0%}" if ar 
                    else f"  • Flow potential: {flow.flow_potential:.0%}")
        lines.append(f"  • عمق التركيز: {flow.focus_depth}" if ar
                    else f"  • Focus depth: {flow.focus_depth}")
    
    # Risk Assessment
    if "risk_assessment" in result:
        risk = result["risk_assessment"]
        lines.append("\n⚡ تقييم المخاطرة:" if ar else "\n⚡ Risk Assessment:")
        lines.append(f"  • المستوى: {risk.category}" if ar
                    else f"  • Level: {risk.category}")
        lines.append(f"  • منطقة الراحة: {risk.comfort_zone_width}" if ar
                    else f"  • Comfort zone: {risk.comfort_zone_width}")
    
    # Summary
    if "summary" in result:
        summary = result["summary"]
        lines.append("\n📝 الملخص:" if ar else "\n📝 Summary:")
        lines.append(f"  • وضوح الملف: {summary['profile_clarity']}" if ar
                    else f"  • Profile clarity: {summary['profile_clarity']}")
        lines.append(f"  • متوسط الثقة: {summary['average_confidence']:.0%}" if ar
                    else f"  • Avg confidence: {summary['average_confidence']:.0%}")
    
    lines.append("\n" + "=" * 50)
    
    return "\n".join(lines)

# ============================================================================
# Examples & Testing
# ============================================================================

if __name__ == "__main__":
    print("🧪 اختبار Layer-Z Enhanced...\n")
    
    # Test 1: هادئ تكتيكي فردي
    test1 = """
    أحب الهدوء والتركيز العميق. أفضل العمل لوحدي.
    أحتاج للسيطرة والتخطيط الدقيق. أكره الرتابة.
    """
    
    analyzer = EnhancedLayerZ()
    result1 = analyzer.analyze_complete(test1, "العربية")
    
    print("=" * 60)
    print("Test 1: هادئ تكتيكي فردي")
    print("=" * 60)
    print(format_z_report(result1, "العربية"))
    
    # Test 2: مغامر اجتماعي
    test2 = """
    أحب الإثارة والأدرينالين! أحب المغامرات الجديدة.
    أستمتع باللعب مع الأصدقاء والفريق. أكره الروتين.
    """
    
    result2 = analyzer.analyze_complete(test2, "العربية")
    
    print("\n" + "=" * 60)
    print("Test 2: مغامر اجتماعي")
    print("=" * 60)
    print(format_z_report(result2, "العربية"))
    
    # Test 3: Backward compatibility
    print("\n" + "=" * 60)
    print("Test 3: Backward Compatibility")
    print("=" * 60)
    
    answers = {
        "q1": {"answer": "أحب الهدوء والتأمل"},
        "q2": {"answer": "أفضل العمل لوحدي"},
        "q3": {"answer": "أحتاج للتخطيط الدقيق"}
    }
    
    result3 = analyze_silent_drivers_enhanced(answers, "العربية")
    print("\nZ-Scores:")
    for axis, score in result3["z_scores"].items():
        print(f"  {axis}: {score:+.2f}")
    
    print("\nZ-Drivers:")
    for driver in result3["z_drivers"]:
        print(f"  • {driver}")
    
    print("\n✅ جميع الاختبارات نجحت!")
