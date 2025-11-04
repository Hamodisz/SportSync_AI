# -*- coding: utf-8 -*-
"""
Supabase Database Client for SportSync
======================================
Client للتواصل مع قاعدة بيانات Supabase
"""

import os
from typing import Optional, Dict, List, Any
from datetime import datetime
import hashlib
import json

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from core.env_utils import _bootstrap_env

_bootstrap_env()


class SupabaseClient:
    """عميل Supabase للتفاعل مع قاعدة البيانات"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.enabled = False
        self._init_client()
    
    def _init_client(self):
        """تهيئة عميل Supabase"""
        if not SUPABASE_AVAILABLE:
            print("[SUPABASE] supabase-py not installed. Install with: pip install supabase")
            return
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print("[SUPABASE] Missing SUPABASE_URL or SUPABASE_KEY in environment")
            return
        
        try:
            self.client = create_client(url, key)
            self.enabled = True
            print(f"[SUPABASE] Connected successfully to {url[:30]}...")
        except Exception as e:
            print(f"[SUPABASE] Failed to connect: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Supabase is enabled and connected"""
        return self.enabled and self.client is not None
    
    # ========================================
    # User Management
    # ========================================
    
    def create_or_get_user(self, user_hash: str, language: str = 'ar', country: str = 'SA') -> Optional[Dict]:
        """إنشاء أو جلب مستخدم"""
        if not self.is_enabled():
            return None
        
        try:
            # Try to get existing user
            result = self.client.table('users').select('*').eq('user_hash', user_hash).execute()
            
            if result.data and len(result.data) > 0:
                # Update last session
                user = result.data[0]
                self.client.table('users').update({
                    'last_session_at': datetime.now().isoformat(),
                    'total_sessions': user['total_sessions'] + 1
                }).eq('id', user['id']).execute()
                return user
            
            # Create new user
            result = self.client.table('users').insert({
                'user_hash': user_hash,
                'language': language,
                'country': country
            }).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"[SUPABASE] Error in create_or_get_user: {e}")
            return None
    
    def generate_user_hash(self, identifier: str) -> str:
        """إنشاء hash للمستخدم (anonymous)"""
        return hashlib.sha256(identifier.encode()).hexdigest()[:32]
    
    # ========================================
    # Quiz Responses
    # ========================================
    
    def save_quiz_responses(
        self,
        user_id: str,
        session_id: str,
        responses: List[Dict[str, Any]]
    ) -> bool:
        """حفظ إجابات الاستبيان"""
        if not self.is_enabled():
            return False
        
        try:
            records = []
            for resp in responses:
                records.append({
                    'user_id': user_id,
                    'session_id': session_id,
                    'question_id': str(resp.get('question_id')),
                    'question_text': resp.get('question_text', ''),
                    'answer_value': str(resp.get('answer')),
                    'answer_index': resp.get('answer_index'),
                    'category': resp.get('category', '')
                })
            
            self.client.table('quiz_responses').insert(records).execute()
            print(f"[SUPABASE] Saved {len(records)} quiz responses")
            return True
            
        except Exception as e:
            print(f"[SUPABASE] Error saving quiz responses: {e}")
            return False
    
    # ========================================
    # User Traits
    # ========================================
    
    def save_user_traits(
        self,
        user_id: str,
        session_id: str,
        traits: Dict[str, float]
    ) -> bool:
        """حفظ السمات النفسية للمستخدم"""
        if not self.is_enabled():
            return False
        
        try:
            record = {
                'user_id': user_id,
                'session_id': session_id,
                **traits  # Unpack all traits
            }
            
            self.client.table('user_traits').insert(record).execute()
            print(f"[SUPABASE] Saved user traits: {len(traits)} traits")
            return True
            
        except Exception as e:
            print(f"[SUPABASE] Error saving user traits: {e}")
            return False
    
    # ========================================
    # Recommendations
    # ========================================
    
    def save_recommendations(
        self,
        user_id: str,
        session_id: str,
        recommendations: List[Dict[str, Any]]
    ) -> bool:
        """حفظ التوصيات"""
        if not self.is_enabled():
            return False
        
        try:
            records = []
            for idx, rec in enumerate(recommendations, 1):
                records.append({
                    'user_id': user_id,
                    'session_id': session_id,
                    'rank': idx,
                    'sport_label': rec.get('sport_label', rec.get('name', 'Unknown')),
                    'sport_category': rec.get('category'),
                    'match_percentage': rec.get('match_percentage', 0),
                    'details': json.dumps(rec, ensure_ascii=False)
                })
            
            self.client.table('recommendations').insert(records).execute()
            print(f"[SUPABASE] Saved {len(records)} recommendations")
            return True
            
        except Exception as e:
            print(f"[SUPABASE] Error saving recommendations: {e}")
            return False
    
    def update_recommendation_interaction(
        self,
        recommendation_id: str,
        clicked: Optional[bool] = None,
        liked: Optional[bool] = None
    ) -> bool:
        """تحديث تفاعل المستخدم مع التوصية"""
        if not self.is_enabled():
            return False
        
        try:
            update_data = {'interaction_time': datetime.now().isoformat()}
            if clicked is not None:
                update_data['clicked'] = clicked
            if liked is not None:
                update_data['liked'] = liked
            
            self.client.table('recommendations').update(update_data).eq('id', recommendation_id).execute()
            return True
            
        except Exception as e:
            print(f"[SUPABASE] Error updating interaction: {e}")
            return False
    
    # ========================================
    # Sport Ratings (Collaborative Filtering)
    # ========================================
    
    def save_sport_rating(
        self,
        user_id: str,
        sport_label: str,
        rating: float,
        was_recommended: bool = False,
        was_clicked: bool = False,
        was_liked: bool = False
    ) -> bool:
        """حفظ أو تحديث تقييم رياضة"""
        if not self.is_enabled():
            return False
        
        try:
            # Upsert (insert or update)
            record = {
                'user_id': user_id,
                'sport_label': sport_label,
                'rating': rating,
                'was_recommended': was_recommended,
                'was_clicked': was_clicked,
                'was_liked': was_liked,
                'confidence': 1.0 if was_liked else 0.7
            }
            
            self.client.table('sport_ratings').upsert(record).execute()
            return True
            
        except Exception as e:
            print(f"[SUPABASE] Error saving sport rating: {e}")
            return False
    
    def get_user_ratings(self, user_id: str) -> List[Dict]:
        """جلب تقييمات المستخدم"""
        if not self.is_enabled():
            return []
        
        try:
            result = self.client.table('sport_ratings').select('*').eq('user_id', user_id).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"[SUPABASE] Error getting user ratings: {e}")
            return []
    
    def get_sport_ratings(self, sport_label: str, limit: int = 100) -> List[Dict]:
        """جلب تقييمات رياضة معينة"""
        if not self.is_enabled():
            return []
        
        try:
            result = self.client.table('sport_ratings') \
                .select('user_id, rating, confidence') \
                .eq('sport_label', sport_label) \
                .limit(limit) \
                .execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"[SUPABASE] Error getting sport ratings: {e}")
            return []
    
    # ========================================
    # Similar Users
    # ========================================
    
    def get_similar_users(self, user_id: str, limit: int = 10) -> List[Dict]:
        """جلب المستخدمين المشابهين"""
        if not self.is_enabled():
            return []
        
        try:
            result = self.client.table('similar_users') \
                .select('similar_user_id, similarity_score, shared_traits') \
                .eq('user_id', user_id) \
                .order('similarity_score', desc=True) \
                .limit(limit) \
                .execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"[SUPABASE] Error getting similar users: {e}")
            return []
    
    def compute_and_save_similar_users(
        self,
        user_id: str,
        similar_users: List[Dict[str, Any]]
    ) -> bool:
        """حفظ المستخدمين المشابهين المحسوبين"""
        if not self.is_enabled():
            return False
        
        try:
            # Delete old similarities
            self.client.table('similar_users').delete().eq('user_id', user_id).execute()
            
            # Insert new
            records = []
            for sim_user in similar_users:
                records.append({
                    'user_id': user_id,
                    'similar_user_id': sim_user['user_id'],
                    'similarity_score': sim_user['score'],
                    'shared_traits': json.dumps(sim_user.get('shared_traits', {}))
                })
            
            if records:
                self.client.table('similar_users').insert(records).execute()
                print(f"[SUPABASE] Saved {len(records)} similar users")
            return True
            
        except Exception as e:
            print(f"[SUPABASE] Error saving similar users: {e}")
            return False
    
    # ========================================
    # Analytics
    # ========================================
    
    def log_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Optional[Dict] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """تسجيل حدث تحليلي"""
        if not self.is_enabled():
            return False
        
        try:
            record = {
                'user_id': user_id,
                'event_type': event_type,
                'event_data': json.dumps(event_data or {}, ensure_ascii=False),
            }
            if session_id:
                record['session_id'] = session_id
            
            self.client.table('analytics_events').insert(record).execute()
            return True
            
        except Exception as e:
            print(f"[SUPABASE] Error logging event: {e}")
            return False
    
    def get_popular_sports(self, limit: int = 20) -> List[Dict]:
        """جلب الرياضات الأكثر شعبية"""
        if not self.is_enabled():
            return []
        
        try:
            result = self.client.table('popular_sports') \
                .select('*') \
                .limit(limit) \
                .execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"[SUPABASE] Error getting popular sports: {e}")
            return []


# Singleton instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client singleton"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


__all__ = ['SupabaseClient', 'get_supabase_client']
