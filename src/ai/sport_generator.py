"""
Sport DNA Generator - Simple OpenAI Version
يولّد رياضات فريدة باستخدام OpenAI GPT-4
"""

import hashlib
import json
from typing import Dict, List, Any
import os
import requests


class SportDNAGenerator:
    """
    يولّد رياضة فريدة 100% لكل مستخدم بناءً على Z-Profile
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
    def generate_unique_sport(self, z_profile: Dict[str, float]) -> Dict[str, Any]:
        """
        توليد رياضة فريدة بناءً على Z-Profile
        """
        # Build prompt
        prompt = self._build_prompt(z_profile)
        
        # Call OpenAI
        try:
            response = self._call_openai(prompt)
            sport = self._parse_response(response)
        except Exception as e:
            print(f"⚠️ Generation error: {e}")
            sport = self._get_fallback_sport(z_profile)
        
        # Add hash
        sport['dna_hash'] = self._generate_hash(sport)
        
        return sport
    
    def _call_openai(self, prompt: str) -> str:
        """
        استدعاء OpenAI API
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': 'أنت خبير ابتكار رياضات فريدة. تجيب فقط بصيغة JSON.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.9,
            'max_tokens': 1000
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    
    def _build_prompt(self, z_profile: Dict[str, float]) -> str:
        """
        بناء prompt
        """
        tech = z_profile.get('technical_intuitive', 0)
        solo = z_profile.get('solo_group', 0)
        calm = z_profile.get('calm_adrenaline', 0)
        
        return f"""ابتكر رياضة جديدة تماماً بناءً على البروفايل التالي:

**البروفايل:**
- Technical: {tech:.2f} {"(تقني)" if tech > 0 else "(حدسي)"}
- Solo: {solo:.2f} {"(فردي)" if solo > 0 else "(جماعي)"}
- Calm: {calm:.2f} {"(هادئ)" if calm > 0 else "(حماسي)"}

**متطلبات:**
✅ رياضة لم تُخترع من قبل
✅ تناسب السعودية
✅ اسم عربي فريد

❌ ممنوع:
- الشطرنج
- رماية السهام
- Airsoft/Paintball
- أي رياضة معروفة

**JSON فقط:**
{{
  "name_ar": "اسم فريد",
  "tagline_ar": "جملة قصيرة",
  "description_ar": "وصف 2-3 جمل",
  "how_to_play": ["خطوة 1", "خطوة 2"],
  "equipment": ["أداة 1"],
  "locations": ["مكان"],
  "innovation_level": 9.0
}}"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response
        """
        # Clean response
        cleaned = response.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # Parse
        return json.loads(cleaned)
    
    def _get_fallback_sport(self, z_profile: Dict[str, float]) -> Dict[str, Any]:
        """
        رياضة احتياطية إذا فشل التوليد
        """
        tech = z_profile.get('technical_intuitive', 0)
        
        if tech > 0.5:
            name = "دوائر الدقة التأملية"
            desc = "رياضة تجمع بين الدقة العالية والهدوء الذهني"
        else:
            name = "تدفق الحركة الحدسية"
            desc = "رياضة تعتمد على الحدس والتفاعل اللحظي"
        
        return {
            'name_ar': name,
            'tagline_ar': "رياضة فريدة مصممة لك",
            'description_ar': desc,
            'how_to_play': ["ابدأ بخطوات بسيطة", "تطور تدريجياً"],
            'equipment': ["أدوات بسيطة متوفرة"],
            'locations': ["قاعات رياضية", "مساحات هادئة"],
            'innovation_level': 8.5
        }
    
    def _generate_hash(self, sport: Dict[str, Any]) -> str:
        """
        Generate unique hash
        """
        text = f"{sport.get('name_ar', '')}{sport.get('description_ar', '')}"
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def validate_uniqueness(self, sport: Dict[str, Any]) -> bool:
        """
        تحقق من الفرادة
        """
        BANNED = [
            'شطرنج', 'chess', 'رماية', 'archery',
            'كرة القدم', 'football', 'airsoft',
            'paintball', 'laser tag', 'دارت', 'bowling'
        ]
        
        text = f"{sport.get('name_ar', '')} {sport.get('description_ar', '')}".lower()
        
        for banned in BANNED:
            if banned in text:
                return False
        
        return True
