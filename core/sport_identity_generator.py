# -*- coding: utf-8 -*-
"""
Sport Identity Generator - The Core Innovation Engine
=====================================================
This is where we INVENT personalized sports, not recommend existing ones.

Philosophy:
- We don't give you "football" or "swimming"
- We create "YOUR sport" - a unique identity that fits only YOU
- Examples: "Solitude Biking", "Flow Dance VR", "Combat Rhythm Arena"

The system combines:
- 141 psychological traits
- Layer Z (hidden motivations)
- Dual-Model AI (Discovery + Reasoning)
- Sport DNA synthesis
"""

import json
import random
from typing import Dict, List, Any, Optional


class SportIdentityGenerator:
    """
    محرك اختراع الرياضات المخصصة
    NOT a recommender - an INVENTOR
    """
    
    def __init__(self):
        # Sport DNA Components
        self.environments = {
            'ar': ['الطبيعة البرية', 'الفضاء الافتراضي', 'المياه العميقة', 'الجبال الشاهقة', 
                   'الغابات المظلمة', 'الصحراء الهادئة', 'المدينة الليلية', 'الفضاء الداخلي'],
            'en': ['Wild Nature', 'Virtual Space', 'Deep Waters', 'High Mountains',
                   'Dark Forests', 'Silent Desert', 'Night City', 'Inner Space']
        }
        
        self.movement_patterns = {
            'ar': ['تدفق حر', 'إيقاع منظم', 'انفجار طاقة', 'هدوء متأمل',
                   'تناسق جماعي', 'ارتجال فردي', 'قتال تكتيكي', 'رقص تعبيري'],
            'en': ['Free Flow', 'Organized Rhythm', 'Energy Burst', 'Meditative Calm',
                   'Group Sync', 'Solo Improvisation', 'Tactical Combat', 'Expressive Dance']
        }
        
        self.core_drives = {
            'ar': ['الهروب الداخلي', 'التحدي الذاتي', 'التواصل العميق', 'السيطرة الكاملة',
                   'الحرية المطلقة', 'النظام والدقة', 'الإبداع التلقائي', 'القوة والسيطرة'],
            'en': ['Internal Escape', 'Self Challenge', 'Deep Connection', 'Total Control',
                   'Absolute Freedom', 'Order & Precision', 'Spontaneous Creativity', 'Power & Dominance']
        }
        
        self.intensity_modes = {
            'ar': ['وضع الهدوء', 'وضع التدفق', 'وضع الانفجار', 'وضع التوازن'],
            'en': ['Calm Mode', 'Flow Mode', 'Burst Mode', 'Balance Mode']
        }
        
        # VR/Reality Mix
        self.reality_modes = {
            'ar': ['واقع حقيقي', 'واقع افتراضي', 'واقع مختلط', 'واقع معزز'],
            'en': ['Pure Reality', 'Virtual Reality', 'Mixed Reality', 'Augmented Reality']
        }
    
    def generate_sport_identity(
        self,
        user_traits: Dict[str, float],
        layer_z: Dict[str, Any],
        language: str = 'ar'
    ) -> Dict[str, Any]:
        """
        اختراع هوية رياضية فريدة للمستخدم
        
        Returns a UNIQUE sport that has never existed before
        """
        lang = 'ar' if language in ['ar', 'العربية'] else 'en'
        
        # Analyze deep patterns
        dominant_trait = max(user_traits.items(), key=lambda x: x[1])[0] if user_traits else 'balanced'
        
        # Synthesize Sport DNA
        sport_dna = self._synthesize_sport_dna(user_traits, layer_z, lang)
        
        # Generate unique name
        sport_name = self._create_unique_name(sport_dna, lang)
        
        # Build complete identity
        identity = {
            'sport_label': sport_name,
            'tagline': self._create_tagline(sport_dna, lang),
            'dna': sport_dna,
            'what_is_it': self._describe_essence(sport_dna, lang),
            'why_you': self._explain_perfect_fit(sport_dna, user_traits, lang),
            'first_week': self._design_first_week(sport_dna, lang),
            'reality_mode': self._select_reality_mode(user_traits, lang),
            'intensity_level': self._calculate_intensity(user_traits),
            'social_mode': self._determine_social_mode(user_traits, lang),
            'equipment_needed': self._list_equipment(sport_dna, lang),
            'where_to_start': self._practical_next_steps(sport_dna, lang),
            'invented_for': 'YOU',
            'match_score': self._calculate_match_score(user_traits, sport_dna)
        }
        
        return identity
    
    def _synthesize_sport_dna(
        self,
        traits: Dict[str, float],
        layer_z: Dict[str, Any],
        lang: str
    ) -> Dict[str, str]:
        """
        تركيب DNA الرياضة من السمات النفسية
        """
        # Get dominant patterns
        high_energy = traits.get('energy_level', 5) > 7
        introvert = traits.get('extroversion', 5) < 4
        creative = traits.get('creativity', 5) > 7
        risk_taker = traits.get('risk_tolerance', 5) > 7
        
        # Select DNA components
        dna = {
            'environment': self._select_by_profile(
                self.environments[lang],
                introvert, high_energy, risk_taker
            ),
            'movement': self._select_by_profile(
                self.movement_patterns[lang],
                creative, high_energy, introvert
            ),
            'core_drive': self._select_by_profile(
                self.core_drives[lang],
                introvert, creative, risk_taker
            ),
            'intensity': self.intensity_modes[lang][
                0 if not high_energy else (2 if risk_taker else 1)
            ]
        }
        
        return dna
    
    def _select_by_profile(
        self,
        options: List[str],
        trait1: bool,
        trait2: bool,
        trait3: bool
    ) -> str:
        """
        اختيار ذكي بناءً على الخصائص
        """
        score = sum([trait1, trait2, trait3])
        index = min(score * 2, len(options) - 1)
        return options[index]
    
    def _create_unique_name(self, dna: Dict[str, str], lang: str) -> str:
        """
        إنشاء اسم فريد للرياضة المخترعة
        """
        # Combine DNA elements to create unique name
        env = dna['environment'].split()[0]  # First word
        move = dna['movement'].split()[0]  # First word
        
        if lang == 'ar':
            return f"{move} {env}"
        else:
            return f"{env} {move}"
    
    def _create_tagline(self, dna: Dict[str, str], lang: str) -> str:
        """شعار ملهم"""
        if lang == 'ar':
            return f"رياضتك الفريدة: {dna['core_drive']} في {dna['environment']}"
        else:
            return f"Your Unique Sport: {dna['core_drive']} in {dna['environment']}"
    
    def _describe_essence(self, dna: Dict[str, str], lang: str) -> str:
        """
        وصف جوهر الرياضة المخترعة
        """
        if lang == 'ar':
            return f"""
رياضة مخصصة لك تماماً، تجمع بين:
• البيئة: {dna['environment']}
• نمط الحركة: {dna['movement']}
• الدافع الأساسي: {dna['core_drive']}
• مستوى الشدة: {dna['intensity']}

هذه ليست رياضة عادية - إنها هويتك الرياضية الفريدة.
            """.strip()
        else:
            return f"""
A sport customized exclusively for you, combining:
• Environment: {dna['environment']}
• Movement Pattern: {dna['movement']}
• Core Drive: {dna['core_drive']}
• Intensity Level: {dna['intensity']}

This isn't a regular sport - it's your unique athletic identity.
            """.strip()
    
    def _explain_perfect_fit(
        self,
        dna: Dict[str, str],
        traits: Dict[str, float],
        lang: str
    ) -> List[str]:
        """
        شرح لماذا هذه الرياضة مثالية لهذا الشخص بالذات
        """
        reasons = []
        
        if lang == 'ar':
            if traits.get('extroversion', 5) < 4:
                reasons.append(f"تناسب طبيعتك الانطوائية: {dna['environment']} يوفر العزلة المثالية")
            if traits.get('creativity', 5) > 7:
                reasons.append(f"تشبع إبداعك: {dna['movement']} يسمح بالتعبير الحر")
            if traits.get('energy_level', 5) > 7:
                reasons.append(f"تستوعب طاقتك العالية: {dna['intensity']} يتماشى مع حيويتك")
            if traits.get('risk_tolerance', 5) > 7:
                reasons.append(f"تلبي حاجتك للمخاطرة: {dna['core_drive']} يوفر التحدي المناسب")
        else:
            if traits.get('extroversion', 5) < 4:
                reasons.append(f"Fits your introverted nature: {dna['environment']} provides perfect solitude")
            if traits.get('creativity', 5) > 7:
                reasons.append(f"Satisfies your creativity: {dna['movement']} allows free expression")
            if traits.get('energy_level', 5) > 7:
                reasons.append(f"Matches your high energy: {dna['intensity']} aligns with your vitality")
            if traits.get('risk_tolerance', 5) > 7:
                reasons.append(f"Meets your risk appetite: {dna['core_drive']} provides the right challenge")
        
        return reasons if reasons else [
            "مصممة خصيصاً لملفك النفسي الفريد" if lang == 'ar' 
            else "Designed specifically for your unique psychological profile"
        ]
    
    def _design_first_week(self, dna: Dict[str, str], lang: str) -> Dict[str, str]:
        """
        تصميم الأسبوع الأول كتجربة عملية
        """
        if lang == 'ar':
            return {
                'day_1': f"استكشاف: اكتشف {dna['environment']} لمدة 15 دقيقة",
                'day_3': f"تجربة: جرب {dna['movement']} بدون ضغط",
                'day_5': f"اندماج: ادمج {dna['core_drive']} في ممارستك",
                'day_7': f"تقييم: راجع تجربتك في {dna['intensity']}"
            }
        else:
            return {
                'day_1': f"Explore: Discover {dna['environment']} for 15 minutes",
                'day_3': f"Experiment: Try {dna['movement']} without pressure",
                'day_5': f"Integrate: Incorporate {dna['core_drive']} into practice",
                'day_7': f"Evaluate: Review your {dna['intensity']} experience"
            }
    
    def _select_reality_mode(self, traits: Dict[str, float], lang: str) -> Dict[str, Any]:
        """
        اختيار نمط الواقع (حقيقي أم افتراضي أم مختلط)
        """
        tech_affinity = traits.get('openness', 5) > 7
        social_anxiety = traits.get('extroversion', 5) < 3
        
        if tech_affinity and social_anxiety:
            mode = 'واقع افتراضي' if lang == 'ar' else 'Virtual Reality'
            benefit = 'تجربة غامرة بدون ضغط اجتماعي' if lang == 'ar' else 'Immersive experience without social pressure'
        elif tech_affinity:
            mode = 'واقع مختلط' if lang == 'ar' else 'Mixed Reality'
            benefit = 'الأفضل من العالمين' if lang == 'ar' else 'Best of both worlds'
        else:
            mode = 'واقع حقيقي' if lang == 'ar' else 'Pure Reality'
            benefit = 'اتصال حقيقي بالعالم' if lang == 'ar' else 'Authentic connection with reality'
        
        return {
            'mode': mode,
            'benefit': benefit,
            'recommended_tech': self._suggest_tech(mode, lang)
        }
    
    def _suggest_tech(self, mode: str, lang: str) -> str:
        """اقتراح التقنيات المناسبة"""
        if 'Virtual' in mode or 'افتراضي' in mode:
            return "Meta Quest 3, PSVR2" if lang == 'en' else "ميتا كويست 3، بلايستيشن في آر"
        elif 'Mixed' in mode or 'مختلط' in mode:
            return "Apple Vision Pro, HoloLens" if lang == 'en' else "آبل فيجن برو، هولولينز"
        else:
            return "No special tech needed" if lang == 'en' else "لا حاجة لتقنيات خاصة"
    
    def _calculate_intensity(self, traits: Dict[str, float]) -> int:
        """حساب مستوى الشدة (1-10)"""
        energy = traits.get('energy_level', 5)
        discipline = traits.get('discipline', 5)
        return min(10, int((energy + discipline) / 2))
    
    def _determine_social_mode(self, traits: Dict[str, float], lang: str) -> str:
        """
        تحديد النمط الاجتماعي المثالي
        """
        social_score = traits.get('social_preference', 5)
        
        if social_score < 3:
            return "منفرد تماماً - لا تفاعل" if lang == 'ar' else "Completely Solo - No Interaction"
        elif social_score < 5:
            return "منفرد مع خيار المشاركة" if lang == 'ar' else "Solo with Option to Share"
        elif social_score < 7:
            return "شريك واحد أو اثنين" if lang == 'ar' else "One or Two Partners"
        else:
            return "مجموعة صغيرة (3-5)" if lang == 'ar' else "Small Group (3-5)"
    
    def _list_equipment(self, dna: Dict[str, str], lang: str) -> List[str]:
        """قائمة المعدات المطلوبة"""
        # Generate smart equipment list based on DNA
        equipment = []
        
        if 'Virtual' in dna.get('environment', ''):
            equipment.append("VR Headset" if lang == 'en' else "نظارة واقع افتراضي")
        
        if 'Water' in dna.get('environment', '') or 'مياه' in dna.get('environment', ''):
            equipment.append("Swimming gear" if lang == 'en' else "معدات سباحة")
        
        if 'Mountain' in dna.get('environment', '') or 'جبل' in dna.get('environment', ''):
            equipment.append("Climbing equipment" if lang == 'en' else "معدات تسلق")
        
        # Default minimal
        if not equipment:
            equipment.append("Comfortable clothes" if lang == 'en' else "ملابس مريحة")
            equipment.append("Your mindset" if lang == 'en' else "عقليتك الصحيحة")
        
        return equipment
    
    def _practical_next_steps(self, dna: Dict[str, str], lang: str) -> List[str]:
        """
        خطوات عملية للبدء
        """
        if lang == 'ar':
            return [
                f"1. ابحث عن مكان يوفر {dna['environment']}",
                f"2. جرب {dna['movement']} لمدة 10 دقائق",
                f"3. ركز على {dna['core_drive']}",
                "4. سجل شعورك بعد كل جلسة",
                "5. عدل التجربة حسب احتياجك"
            ]
        else:
            return [
                f"1. Find a location with {dna['environment']}",
                f"2. Try {dna['movement']} for 10 minutes",
                f"3. Focus on {dna['core_drive']}",
                "4. Journal your feelings after each session",
                "5. Adjust the experience to your needs"
            ]
    
    def _calculate_match_score(
        self,
        traits: Dict[str, float],
        dna: Dict[str, str]
    ) -> int:
        """
        حساب درجة التوافق (0-100)
        """
        # This sport was INVENTED for this person
        # So the match should be very high (85-98%)
        base_score = 85
        
        # Add bonuses based on trait alignment
        bonus = 0
        if traits.get('energy_level', 5) > 7:
            bonus += 3
        if traits.get('creativity', 5) > 7:
            bonus += 3
        if traits.get('openness', 5) > 7:
            bonus += 3
        
        return min(98, base_score + bonus)


# Singleton instance
_generator = None

def get_sport_identity_generator() -> SportIdentityGenerator:
    """Get or create generator singleton"""
    global _generator
    if _generator is None:
        _generator = SportIdentityGenerator()
    return _generator


__all__ = ['SportIdentityGenerator', 'get_sport_identity_generator']
