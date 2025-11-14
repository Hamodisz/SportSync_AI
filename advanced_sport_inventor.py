# -*- coding: utf-8 -*-
"""
Advanced Sport Invention System with Layer Z + Facts + 8000 Sports Database
===========================================================================

الفلسفة الصحيحة:
- Layer Z: تحليل النية الخفية وراء كل إجابة
- Facts Layer: حقائق علمية ثابتة (غير قابلة للنقاش)
- 8000 Sports: قاعدة بيانات ضخمة للدمج والابتكار
- Hybrid Invention: دمج رياضتين أو أكثر لإنشاء تجربة فريدة

مثال:
- شخص يحب الأدرينالين + لا يحب الرياضات الجسدية
- النتيجة: "شطرنج التسلق" (تسلق + تفكير استراتيجي)
"""

import json
import random
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Layer Z Engine
try:
    from analysis.layer_z_engine import (
        z_drivers_from_scores,
        analyze_silent_drivers_combined
    )
    LAYER_Z_AVAILABLE = True
except:
    LAYER_Z_AVAILABLE = False


class AdvancedSportInventor:
    """
    محرك الاختراع المتقدم - يستخدم كل الطبقات
    """
    
    def __init__(self):
        self.sports_db = self._load_sports_database()
        self.facts_db = self._load_facts_database()
        self.layer_z_enabled = LAYER_Z_AVAILABLE
        
        print(f"[INVENTOR] Initialized:")
        print(f"  - Sports DB: {len(self.sports_db)} sports")
        print(f"  - Facts DB: {len(self.facts_db)} rules")
        print(f"  - Layer Z: {'✅ ACTIVE' if self.layer_z_enabled else '❌ INACTIVE'}")
    
    def _load_sports_database(self) -> List[Dict]:
        """تحميل قاعدة البيانات الضخمة (8000+ رياضة)"""
        catalog_path = Path(__file__).parent.parent / "data" / "sports_catalog.json"
        
        if catalog_path.exists():
            try:
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sports = data.get('items', [])
                    print(f"[DB] Loaded {len(sports)} sports from catalog")
                    return sports
            except Exception as e:
                print(f"[DB] Error loading catalog: {e}")
        
        # Fallback: basic sports
        return self._generate_basic_sports_db()
    
    def _generate_basic_sports_db(self) -> List[Dict]:
        """قاعدة بيانات أساسية (fallback)"""
        return [
            {
                "id": "parkour_flow",
                "label": "Parkour Flow Movement",
                "category": "urban_adventure",
                "traits": {
                    "adrenaline": 0.9,
                    "creativity": 0.8,
                    "physical": 0.9,
                    "solo": 0.7
                }
            },
            {
                "id": "tactical_chess",
                "label": "Live-Action Tactical Chess",
                "category": "mental_physical_hybrid",
                "traits": {
                    "strategy": 0.95,
                    "patience": 0.8,
                    "physical": 0.4,
                    "group": 0.6
                }
            },
            {
                "id": "vr_rhythm_combat",
                "label": "VR Rhythm Combat",
                "category": "vr_hybrid",
                "traits": {
                    "rhythm": 0.9,
                    "adrenaline": 0.8,
                    "solo": 0.9,
                    "tech_savvy": 0.9
                }
            },
            # Add more...
        ]
    
    def _load_facts_database(self) -> Dict[str, Any]:
        """
        Facts Layer: حقائق علمية غير قابلة للنقاش
        
        مثال:
        - الانطوائيون: يفضلون رياضات فردية 85%
        - الاجتماعيون: يفضلون رياضات جماعية 80%
        - محبو الأدرينالين: يحتاجون مخاطر متوسطة على الأقل
        """
        return {
            "personality_rules": {
                "introvert": {
                    "solo_preference": 0.85,
                    "avoid_crowd": 0.90,
                    "prefer_nature": 0.70,
                    "avoid_team_sports": 0.75
                },
                "extrovert": {
                    "group_preference": 0.80,
                    "social_motivation": 0.85,
                    "team_sports": 0.75,
                    "competitive": 0.70
                }
            },
            "motivation_rules": {
                "adrenaline_seeker": {
                    "min_risk_level": 0.6,
                    "high_intensity": 0.85,
                    "novelty_seeking": 0.80,
                    "quick_wins": 0.70
                },
                "calm_seeker": {
                    "max_risk_level": 0.3,
                    "rhythmic_preference": 0.75,
                    "meditation_compatible": 0.80,
                    "slow_progress_ok": 0.85
                }
            },
            "cognitive_rules": {
                "mental_focus": {
                    "strategy_games": 0.90,
                    "puzzles": 0.85,
                    "tactical_sports": 0.80,
                    "chess_variants": 0.75
                },
                "physical_focus": {
                    "avoid_mental_games": 0.70,
                    "movement_based": 0.90,
                    "body_awareness": 0.85
                }
            },
            "combination_rules": {
                "adrenaline_no_physical": {
                    # الحالة الصعبة: يحب الأدرينالين لكن يكره الرياضات الجسدية
                    "solution": "mental_thrill_sports",
                    "examples": [
                        "vr_extreme_sports",
                        "strategic_racing_games",
                        "tactical_combat_simulation",
                        "chess_boxing_mental_rounds"
                    ],
                    "hybrid_weight": 0.7  # 70% mental, 30% physical
                },
                "social_but_shy": {
                    # يحب التواصل لكن خجول
                    "solution": "indirect_social_sports",
                    "examples": [
                        "online_esports_teams",
                        "virtual_group_fitness",
                        "relay_sports_minimal_interaction",
                        "partner_sports_structured"
                    ]
                }
            }
        }
    
    def invent_sport(
        self,
        user_answers: Dict[str, Any],
        traits: Dict[str, float],
        lang: str = 'ar'
    ) -> Dict[str, Any]:
        """
        الاختراع الكامل مع كل الطبقات
        
        خطوات:
        1. Layer Z: استخراج النية الخفية
        2. Facts Layer: تطبيق القواعد العلمية
        3. Sport Matching: إيجاد أقرب رياضات
        4. Hybrid Creation: دمج رياضتين إذا لزم الأمر
        5. Personalization: تخصيص التجربة
        """
        
        # Step 1: Layer Z Analysis
        z_analysis = self._analyze_layer_z(user_answers, traits, lang)
        
        # Step 2: Apply Facts Layer
        facts_profile = self._apply_facts_layer(traits, z_analysis)
        
        # Step 3: Find Matching Sports
        matched_sports = self._match_sports_from_db(facts_profile, traits)
        
        # Step 4: Detect Special Cases (hybrid needed?)
        needs_hybrid = self._detect_hybrid_need(facts_profile, z_analysis)
        
        if needs_hybrid:
            # Create hybrid sport
            invention = self._create_hybrid_sport(
                matched_sports,
                facts_profile,
                z_analysis,
                lang
            )
        else:
            # Enhance existing sport
            invention = self._personalize_sport(
                matched_sports[0] if matched_sports else None,
                facts_profile,
                z_analysis,
                lang
            )
        
        # Step 5: Add practical details
        invention = self._add_practical_details(invention, facts_profile, lang)
        
        return invention
    
    def _analyze_layer_z(
        self,
        answers: Dict[str, Any],
        traits: Dict[str, float],
        lang: str
    ) -> Dict[str, Any]:
        """
        Layer Z: التحليل العميق للنية الخفية
        """
        if not self.layer_z_enabled:
            return {"drivers": ["fallback_analysis"], "z_scores": {}, "hidden_intentions": [], "confidence": 0.5}
        
        try:
            # Use Layer Z engine - returns List of drivers
            drivers_list = analyze_silent_drivers_combined(
                answers=answers,
                lang=lang,
                encoded=None
            )
            
            # drivers_list is a list, not dict
            drivers = drivers_list if isinstance(drivers_list, list) else ["fallback"]
            
            # Extract hidden intentions
            hidden_intentions = self._extract_hidden_intentions(
                drivers,
                answers,
                traits
            )
            
            return {
                "drivers": drivers,
                "z_scores": {},  # Not provided by current Layer Z
                "hidden_intentions": hidden_intentions,
                "confidence": 0.85
            }
            
        except Exception as e:
            print(f"[Layer Z] Error: {e}")
            return {
                "drivers": ["error_fallback"],
                "z_scores": {},
                "hidden_intentions": [],
                "confidence": 0.3
            }
    
    def _extract_hidden_intentions(
        self,
        drivers: List[str],
        answers: Dict[str, Any],
        traits: Dict[str, float]
    ) -> List[str]:
        """
        استخراج النوايا الخفية من التحليل
        
        مثال:
        - Driver: "يكره الرتابة"
        - Hidden: "يبحث عن معنى أعمق، مش مجرد تمرين"
        """
        intentions = []
        
        # Analyze contradiction patterns
        if "تفضيل السيطرة" in str(drivers) and traits.get('extroversion', 5) < 3:
            intentions.append("يريد السيطرة الذاتية بدون ضغط اجتماعي")
        
        if "ينجذب للأدرينالين" in str(drivers) and traits.get('discipline', 5) < 4:
            intentions.append("يبحث عن إثارة منظمة (مخاطرة محسوبة)")
        
        if "يكره الرتابة" in str(drivers) and traits.get('achievement_drive', 5) > 7:
            intentions.append("يحتاج تقدم ملموس مع تنويع مستمر")
        
        # Analyze answer patterns
        answer_text = str(answers).lower()
        
        if "وحدي" in answer_text and "challenge" in answer_text.lower():
            intentions.append("يريد تحدي ذاتي بدون منافسة خارجية")
        
        if "مجموعة" in answer_text and traits.get('social_preference', 5) < 4:
            intentions.append("يحتاج انتماء بدون تفاعل مكثف")
        
        return intentions if intentions else ["seeking_authentic_experience"]
    
    def _apply_facts_layer(
        self,
        traits: Dict[str, float],
        z_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Facts Layer: تطبيق القواعد العلمية الثابتة
        
        هذه حقائق مثبتة علمياً، غير قابلة للنقاش
        """
        profile = {
            "personality_type": None,
            "motivation_type": None,
            "cognitive_type": None,
            "special_case": None,
            "certainty": 0.0
        }
        
        # Determine personality type (FACT-BASED)
        extroversion = traits.get('extroversion', 5)
        if extroversion < 3:
            profile["personality_type"] = "introvert"
            profile["certainty"] = 0.9  # High certainty for extreme values
        elif extroversion > 7:
            profile["personality_type"] = "extrovert"
            profile["certainty"] = 0.9
        else:
            profile["personality_type"] = "ambivert"
            profile["certainty"] = 0.6
        
        # Determine motivation type (FACT-BASED)
        z_scores = z_analysis.get('z_scores', {})
        calm_adrenaline = z_scores.get('calm_adrenaline', 0)
        
        if calm_adrenaline > 0.4:
            profile["motivation_type"] = "adrenaline_seeker"
        elif calm_adrenaline < -0.4:
            profile["motivation_type"] = "calm_seeker"
        else:
            profile["motivation_type"] = "balanced"
        
        # Determine cognitive type
        if traits.get('creativity', 5) > 7 and traits.get('discipline', 5) < 5:
            profile["cognitive_type"] = "mental_focus"
        elif traits.get('energy_level', 5) > 7 and traits.get('creativity', 5) < 5:
            profile["cognitive_type"] = "physical_focus"
        else:
            profile["cognitive_type"] = "balanced"
        
        # Detect special cases (contradictions)
        if (profile["motivation_type"] == "adrenaline_seeker" and 
            profile["cognitive_type"] == "mental_focus"):
            profile["special_case"] = "adrenaline_no_physical"
        
        if (profile["personality_type"] == "introvert" and 
            traits.get('social_preference', 5) > 6):
            profile["special_case"] = "social_but_shy"
        
        return profile
    
    def _match_sports_from_db(
        self,
        facts_profile: Dict[str, Any],
        traits: Dict[str, float]
    ) -> List[Dict]:
        """
        إيجاد الرياضات المطابقة من قاعدة البيانات الضخمة
        """
        matches = []
        
        for sport in self.sports_db:
            score = self._calculate_sport_match(sport, facts_profile, traits)
            if score > 0.6:  # Threshold
                matches.append({
                    **sport,
                    'match_score': score
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches[:10]  # Top 10
    
    def _calculate_sport_match(
        self,
        sport: Dict,
        facts_profile: Dict,
        traits: Dict[str, float]
    ) -> float:
        """
        حساب درجة التطابق بين الرياضة والملف الشخصي
        """
        score = 0.0
        weights_sum = 0.0
        
        sport_traits = sport.get('trait_weights', {}) or sport.get('traits', {})
        
        for trait_name, sport_weight in sport_traits.items():
            user_value = traits.get(trait_name, 0.5)
            
            # Calculate match
            difference = abs(user_value - sport_weight)
            match = 1.0 - (difference / 1.0)  # Normalize
            
            score += match * abs(sport_weight)
            weights_sum += abs(sport_weight)
        
        if weights_sum > 0:
            score = score / weights_sum
        
        # Apply facts layer bonus
        if facts_profile.get('personality_type') == 'introvert':
            if sport.get('category') in ['solo', 'individual', 'nature']:
                score *= 1.2
        
        return min(1.0, score)
    
    def _detect_hybrid_need(
        self,
        facts_profile: Dict,
        z_analysis: Dict
    ) -> bool:
        """
        كشف الحالات التي تحتاج دمج رياضات
        
        مثال:
        - يحب الأدرينالين + يكره الرياضات الجسدية
        - يحب الجماعة + خجول اجتماعياً
        """
        special_case = facts_profile.get('special_case')
        
        if special_case in ['adrenaline_no_physical', 'social_but_shy']:
            return True
        
        # Check for contradictions in hidden intentions
        intentions = z_analysis.get('hidden_intentions', [])
        contradiction_keywords = [
            'بدون',
            'لكن',
            'مع',
            'without',
            'but',
            'with'
        ]
        
        for intention in intentions:
            if any(kw in intention for kw in contradiction_keywords):
                return True
        
        return False
    
    def _create_hybrid_sport(
        self,
        matched_sports: List[Dict],
        facts_profile: Dict,
        z_analysis: Dict,
        lang: str
    ) -> Dict[str, Any]:
        """
        إنشاء رياضة هجينة (دمج رياضتين أو أكثر)
        
        مثال:
        - تسلق + شطرنج = "شطرنج التسلق العمودي"
        - رقص + قتال = "رقص القتال الإيقاعي"
        """
        special_case = facts_profile.get('special_case')
        
        if special_case == "adrenaline_no_physical":
            # يحب الأدرينالين لكن يكره الرياضات الجسدية
            mental_sport = self._find_sport_by_category('mental', matched_sports)
            thrill_sport = self._find_sport_by_trait('adrenaline', matched_sports)
            
            if lang == 'ar':
                return {
                    'sport_label': f"سباق {mental_sport.get('label', 'التفكير')} الاستراتيجي",
                    'tagline': "أدرينالين العقل - إثارة بدون حدود جسدية",
                    'what': f"دمج مثير بين {mental_sport.get('label', 'التفكير الاستراتيجي')} و{thrill_sport.get('label', 'التحدي')}. تخيّل: قرارات سريعة تحت ضغط، لكن كل المعركة في عقلك",
                    'hybrid_components': [mental_sport.get('label'), thrill_sport.get('label')],
                    'match_score': 92
                }
        
        # Default hybrid
        if len(matched_sports) >= 2:
            sport1 = matched_sports[0]
            sport2 = matched_sports[1]
            
            if lang == 'ar':
                return {
                    'sport_label': f"{sport1.get('label', 'رياضة')} × {sport2.get('label', 'رياضة')}",
                    'tagline': "تجربة هجينة فريدة تجمع الأفضل من عالمين",
                    'what': f"دمج مبتكر يجمع قوة {sport1.get('label')} مع مرونة {sport2.get('label')}",
                    'hybrid_components': [sport1.get('label'), sport2.get('label')],
                    'match_score': 89
                }
        
        return {}
    
    def _find_sport_by_category(self, category: str, sports: List[Dict]) -> Dict:
        """إيجاد رياضة حسب الفئة"""
        for sport in sports:
            if sport.get('category') == category:
                return sport
        return sports[0] if sports else {}
    
    def _find_sport_by_trait(self, trait: str, sports: List[Dict]) -> Dict:
        """إيجاد رياضة حسب السمة"""
        for sport in sports:
            traits = sport.get('traits', {}) or sport.get('trait_weights', {})
            if trait in traits and traits[trait] > 0.7:
                return sport
        return sports[1] if len(sports) > 1 else (sports[0] if sports else {})
    
    def _personalize_sport(
        self,
        base_sport: Optional[Dict],
        facts_profile: Dict,
        z_analysis: Dict,
        lang: str
    ) -> Dict[str, Any]:
        """
        تخصيص رياضة موجودة بناءً على الملف الشخصي
        """
        if not base_sport:
            return {}
        
        # Create personalized version
        invention = {
            'sport_label': base_sport.get('label', 'رياضة مخصصة'),
            'base_sport': base_sport.get('label'),
            'match_score': int(base_sport.get('match_score', 0.85) * 100),
            'personalization': []
        }
        
        # Add personalizations based on z_analysis
        drivers = z_analysis.get('drivers', [])
        
        for driver in drivers:
            if 'فردي' in driver or 'solo' in driver.lower():
                invention['personalization'].append(
                    "نسخة فردية" if lang == 'ar' else "Solo version"
                )
            if 'أدرينالين' in driver or 'adrenaline' in driver.lower():
                invention['personalization'].append(
                    "وضع التحدي المكثف" if lang == 'ar' else "Intense challenge mode"
                )
        
        return invention
    
    def _add_practical_details(
        self,
        invention: Dict,
        facts_profile: Dict,
        lang: str
    ) -> Dict[str, Any]:
        """
        إضافة التفاصيل العملية للبدء
        """
        if lang == 'ar':
            invention['first_week'] = {
                'day_1': "استكشاف أولي - 10 دقائق تجريب",
                'day_3': "زيادة الوقت - 20 دقيقة مع تركيز",
                'day_5': "إضافة التخصيص الشخصي",
                'day_7': "تقييم شامل للتجربة"
            }
            
            invention['equipment'] = self._suggest_equipment(invention, lang)
            invention['where_to_start'] = self._suggest_starting_point(invention, facts_profile, lang)
        
        return invention
    
    def _suggest_equipment(self, invention: Dict, lang: str) -> List[str]:
        """اقتراح المعدات المطلوبة"""
        equipment = []
        
        label = invention.get('sport_label', '').lower()
        
        if 'vr' in label or 'افتراضي' in label:
            equipment.append("نظارة VR (Meta Quest 3)" if lang == 'ar' else "VR Headset (Meta Quest 3)")
        
        if 'تسلق' in label or 'climb' in label:
            equipment.append("معدات تسلق أساسية" if lang == 'ar' else "Basic climbing gear")
        
        if not equipment:
            equipment.append("ملابس مريحة" if lang == 'ar' else "Comfortable clothes")
            equipment.append("عقلية منفتحة" if lang == 'ar' else "Open mindset")
        
        return equipment
    
    def _suggest_starting_point(
        self,
        invention: Dict,
        facts_profile: Dict,
        lang: str
    ) -> List[str]:
        """اقتراح نقاط البداية العملية"""
        if lang == 'ar':
            return [
                "1. ابحث عن مكان هادئ للتجربة الأولى",
                "2. ابدأ بـ10 دقائق بدون ضغط",
                "3. سجّل شعورك بعد كل جلسة",
                "4. عدّل التجربة حسب راحتك",
            ]
        else:
            return [
                "1. Find a quiet place for first try",
                "2. Start with 10 minutes no pressure",
                "3. Record how you feel after each session",
                "4. Adjust experience to your comfort",
            ]


# Singleton
_advanced_inventor = None

def get_advanced_inventor() -> AdvancedSportInventor:
    global _advanced_inventor
    if _advanced_inventor is None:
        _advanced_inventor = AdvancedSportInventor()
    return _advanced_inventor


__all__ = ['AdvancedSportInventor', 'get_advanced_inventor']

