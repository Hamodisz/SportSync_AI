# -*- coding: utf-8 -*-
"""
Collaborative Filtering Engine for SportSync
============================================
نظام توصيات تعاوني يتعلم من تفضيلات المستخدمين المشابهين
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[CF] scikit-learn not available. Install with: pip install scikit-learn")


class CollaborativeFilteringEngine:
    """محرك التوصيات التعاونية"""
    
    def __init__(self, supabase_client=None):
        self.db = supabase_client
        self.user_item_matrix = {}  # user_id -> {sport: rating}
        self.item_users_matrix = {}  # sport -> {user_id: rating}
        self.user_similarities = {}  # user_id -> [(similar_user_id, score)]
        
    def is_available(self) -> bool:
        """Check if CF is available"""
        return SKLEARN_AVAILABLE and self.db is not None and self.db.is_enabled()
    
    # ========================================
    # Data Loading
    # ========================================
    
    def load_ratings_from_db(self, min_ratings: int = 5):
        """تحميل التقييمات من قاعدة البيانات"""
        if not self.is_available():
            print("[CF] Not available - missing dependencies or database")
            return
        
        try:
            # Get all ratings
            result = self.db.client.table('sport_ratings') \
                .select('user_id, sport_label, rating, confidence') \
                .execute()
            
            if not result.data:
                print("[CF] No ratings found in database")
                return
            
            # Build matrices
            self.user_item_matrix = defaultdict(dict)
            self.item_users_matrix = defaultdict(dict)
            
            for row in result.data:
                user_id = row['user_id']
                sport = row['sport_label']
                rating = float(row['rating']) * float(row.get('confidence', 1.0))
                
                self.user_item_matrix[user_id][sport] = rating
                self.item_users_matrix[sport][user_id] = rating
            
            # Filter users with few ratings
            self.user_item_matrix = {
                user_id: ratings 
                for user_id, ratings in self.user_item_matrix.items()
                if len(ratings) >= min_ratings
            }
            
            print(f"[CF] Loaded {len(self.user_item_matrix)} users, {len(self.item_users_matrix)} sports")
            
        except Exception as e:
            print(f"[CF] Error loading ratings: {e}")
    
    # ========================================
    # User Similarity Computation
    # ========================================
    
    def compute_user_similarity(
        self,
        user_id: str,
        top_k: int = 20
    ) -> List[Tuple[str, float]]:
        """حساب المستخدمين الأكثر تشابهاً"""
        if not self.is_available():
            return []
        
        if user_id not in self.user_item_matrix:
            print(f"[CF] User {user_id[:8]}... not found in matrix")
            return []
        
        user_ratings = self.user_item_matrix[user_id]
        similarities = []
        
        # Compare with all other users
        for other_user_id, other_ratings in self.user_item_matrix.items():
            if other_user_id == user_id:
                continue
            
            # Find common sports
            common_sports = set(user_ratings.keys()) & set(other_ratings.keys())
            
            if len(common_sports) < 2:  # Need at least 2 common items
                continue
            
            # Build vectors for common sports
            vec1 = [user_ratings[sport] for sport in common_sports]
            vec2 = [other_ratings[sport] for sport in common_sports]
            
            # Compute cosine similarity
            similarity = self._cosine_similarity(vec1, vec2)
            
            if similarity > 0.3:  # Threshold for meaningful similarity
                similarities.append((other_user_id, similarity))
        
        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """حساب cosine similarity بين متجهين"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    # ========================================
    # Recommendation Generation
    # ========================================
    
    def recommend_for_user(
        self,
        user_id: str,
        n_recommendations: int = 10,
        exclude_rated: bool = True
    ) -> List[Dict[str, any]]:
        """توصيات مخصصة للمستخدم بناءً على المستخدمين المشابهين"""
        if not self.is_available():
            return []
        
        # Get similar users
        similar_users = self.compute_user_similarity(user_id, top_k=20)
        
        if not similar_users:
            print(f"[CF] No similar users found for {user_id[:8]}...")
            return self._recommend_popular(n_recommendations)
        
        # Get user's already rated sports
        user_rated = set(self.user_item_matrix.get(user_id, {}).keys())
        
        # Aggregate scores from similar users
        sport_scores = defaultdict(float)
        sport_weights = defaultdict(float)
        
        for similar_user_id, similarity in similar_users:
            similar_ratings = self.user_item_matrix.get(similar_user_id, {})
            
            for sport, rating in similar_ratings.items():
                if exclude_rated and sport in user_rated:
                    continue
                
                sport_scores[sport] += rating * similarity
                sport_weights[sport] += similarity
        
        # Calculate weighted average
        recommendations = []
        for sport, total_score in sport_scores.items():
            if sport_weights[sport] > 0:
                avg_score = total_score / sport_weights[sport]
                recommendations.append({
                    'sport_label': sport,
                    'predicted_rating': round(avg_score, 2),
                    'confidence': min(1.0, sport_weights[sport] / 10.0),  # Normalize
                    'based_on_users': len([s for s, _ in similar_users if sport in self.user_item_matrix.get(s, {})])
                })
        
        # Sort by predicted rating
        recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)
        
        return recommendations[:n_recommendations]
    
    def _recommend_popular(self, n: int = 10) -> List[Dict]:
        """التوصية بالرياضات الأكثر شعبية (fallback)"""
        if not self.db or not self.db.is_enabled():
            return []
        
        try:
            popular = self.db.get_popular_sports(limit=n)
            return [
                {
                    'sport_label': sport['sport_label'],
                    'predicted_rating': float(sport.get('avg_rating', 3.5)),
                    'confidence': 0.5,
                    'based_on_users': int(sport.get('unique_users', 0))
                }
                for sport in popular
            ]
        except Exception as e:
            print(f"[CF] Error getting popular sports: {e}")
            return []
    
    # ========================================
    # Hybrid Recommendations
    # ========================================
    
    def hybrid_recommend(
        self,
        user_id: str,
        content_based_recs: List[Dict],
        n_recommendations: int = 5,
        cf_weight: float = 0.4
    ) -> List[Dict]:
        """دمج التوصيات التعاونية مع التوصيات المبنية على المحتوى"""
        if not self.is_available():
            return content_based_recs[:n_recommendations]
        
        # Get collaborative filtering recommendations
        cf_recs = self.recommend_for_user(user_id, n_recommendations=20)
        
        if not cf_recs:
            return content_based_recs[:n_recommendations]
        
        # Create lookup for CF scores
        cf_scores = {rec['sport_label']: rec['predicted_rating'] for rec in cf_recs}
        
        # Combine scores
        hybrid_scores = []
        for cb_rec in content_based_recs:
            sport_label = cb_rec.get('sport_label', cb_rec.get('name', ''))
            
            # Content-based score (from match percentage)
            cb_score = cb_rec.get('match_percentage', 50) / 100.0 * 5.0  # Normalize to 0-5
            
            # Collaborative filtering score
            cf_score = cf_scores.get(sport_label, 2.5)  # Default neutral
            
            # Hybrid score
            hybrid_score = (1 - cf_weight) * cb_score + cf_weight * cf_score
            
            hybrid_scores.append({
                **cb_rec,
                'hybrid_score': hybrid_score,
                'cf_score': cf_score,
                'cb_score': cb_score,
                'has_cf_data': sport_label in cf_scores
            })
        
        # Sort by hybrid score
        hybrid_scores.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return hybrid_scores[:n_recommendations]
    
    # ========================================
    # Update & Maintenance
    # ========================================
    
    def update_user_rating(
        self,
        user_id: str,
        sport_label: str,
        rating: float,
        save_to_db: bool = True
    ):
        """تحديث تقييم المستخدم"""
        # Update local matrix
        if user_id not in self.user_item_matrix:
            self.user_item_matrix[user_id] = {}
        self.user_item_matrix[user_id][sport_label] = rating
        
        if sport_label not in self.item_users_matrix:
            self.item_users_matrix[sport_label] = {}
        self.item_users_matrix[sport_label][user_id] = rating
        
        # Save to database
        if save_to_db and self.db and self.db.is_enabled():
            self.db.save_sport_rating(
                user_id=user_id,
                sport_label=sport_label,
                rating=rating
            )
        
        print(f"[CF] Updated rating: {sport_label} = {rating} for user {user_id[:8]}...")
    
    def refresh_data(self):
        """إعادة تحميل البيانات من قاعدة البيانات"""
        print("[CF] Refreshing data...")
        self.load_ratings_from_db()


__all__ = ['CollaborativeFilteringEngine']
