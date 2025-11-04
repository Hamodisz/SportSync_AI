# -*- coding: utf-8 -*-
"""
users/database.py
----------------
Database manager for user system using PostgreSQL/Supabase.
Handles CRUD operations, caching, and connection pooling.

© Sports Sync AI - 2025
"""

from __future__ import annotations
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool, Connection
from pydantic import ValidationError

from users.models import (
    UserProfile, SportIdentityCard, SportFeedback,
    UserActivity, ProgressMetrics, AccountStatus
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Async PostgreSQL database manager with connection pooling"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self._pool: Optional[Pool] = None
        self._cache: Dict[str, Any] = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes
    
    async def initialize(self):
        """Initialize database connection pool"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database connection pool initialized")
    
    async def close(self):
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def _get_connection(self) -> Connection:
        """Get database connection from pool"""
        if not self._pool:
            await self.initialize()
        
        async with self._pool.acquire() as conn:
            yield conn
    
    # ==================== User CRUD Operations ====================
    
    async def create_user(
        self,
        email: str,
        name: str,
        password_hash: str,
        language: str = "العربية"
    ) -> UserProfile:
        """Create new user account"""
        user_id = self._generate_user_id()
        
        async with self._get_connection() as conn:
            # Check if email exists
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", email
            )
            if existing:
                raise ValueError(f"Email {email} already registered")
            
            # Insert user
            await conn.execute(
                """
                INSERT INTO users (
                    id, email, name, account_status, 
                    subscription_tier, created_at, last_login,
                    preferences
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                user_id, email, name, AccountStatus.ACTIVE.value,
                "free", datetime.utcnow(), datetime.utcnow(),
                json.dumps({"language": language})
            )
            
            # Also store password hash in separate secure table
            await conn.execute(
                "INSERT INTO user_credentials (user_id, password_hash) VALUES ($1, $2)",
                user_id, password_hash
            )
        
        logger.info(f"User created: {user_id} ({email})")
        return await self.get_user_by_id(user_id)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID"""
        # Check cache first
        cache_key = f"user:{user_id}"
        if cache_key in self._cache:
            cached_data, cached_at = self._cache[cache_key]
            if (datetime.utcnow() - cached_at).seconds < self._cache_ttl:
                return UserProfile(**cached_data)
        
        async with self._get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1", user_id
            )
            
            if not row:
                return None
            
            user_data = dict(row)
            
            # Load related data
            user_data['sport_identities'] = await self._load_sport_identities(conn, user_id)
            user_data['sport_feedback'] = await self._load_sport_feedback(conn, user_id)
            
            # Parse JSON fields
            user_data['preferences'] = json.loads(user_data.get('preferences', '{}'))
            user_data['progress'] = json.loads(user_data.get('progress', '{}'))
            user_data['layer_z_profile'] = json.loads(user_data.get('layer_z_profile') or 'null')
            user_data['metadata'] = json.loads(user_data.get('metadata', '{}'))
            
            try:
                user = UserProfile(**user_data)
                # Cache it
                self._cache[cache_key] = (user.dict(), datetime.utcnow())
                return user
            except ValidationError as e:
                logger.error(f"User data validation failed for {user_id}: {e}")
                return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserProfile]:
        """Get user by email"""
        async with self._get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", email
            )
            if row:
                return await self.get_user_by_id(row['id'])
        return None
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> UserProfile:
        """Update user profile"""
        # Clear cache
        cache_key = f"user:{user_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        # Build SET clause dynamically
        set_clauses = []
        values = []
        param_idx = 1
        
        for key, value in updates.items():
            if key in ['preferences', 'metadata', 'progress', 'layer_z_profile']:
                value = json.dumps(value)
            
            set_clauses.append(f"{key} = ${param_idx}")
            values.append(value)
            param_idx += 1
        
        values.append(user_id)  # For WHERE clause
        
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ${param_idx}"
        
        async with self._get_connection() as conn:
            await conn.execute(query, *values)
        
        logger.info(f"User updated: {user_id}")
        return await self.get_user_by_id(user_id)
    
    async def delete_user(self, user_id: str):
        """Soft delete user (mark as deleted)"""
        await self.update_user(user_id, {
            'account_status': AccountStatus.DELETED.value
        })
        logger.info(f"User deleted: {user_id}")
    
    # ==================== Sport Identity Operations ====================
    
    async def save_sport_identity(
        self,
        user_id: str,
        sport_card: SportIdentityCard
    ):
        """Save sport recommendation to user profile"""
        async with self._get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO sport_identities (
                    user_id, sport_label, category, card_data, recommended_at
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                user_id,
                sport_card.sport_label,
                sport_card.category,
                json.dumps(sport_card.dict()),
                sport_card.recommended_at
            )
        
        # Clear cache
        cache_key = f"user:{user_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        logger.info(f"Sport identity saved for user {user_id}: {sport_card.sport_label}")
    
    async def _load_sport_identities(
        self,
        conn: Connection,
        user_id: str
    ) -> List[SportIdentityCard]:
        """Load user's sport identities"""
        rows = await conn.fetch(
            """
            SELECT card_data FROM sport_identities 
            WHERE user_id = $1 
            ORDER BY recommended_at DESC
            """,
            user_id
        )
        
        identities = []
        for row in rows:
            try:
                identities.append(SportIdentityCard(**json.loads(row['card_data'])))
            except Exception as e:
                logger.error(f"Failed to parse sport identity: {e}")
        
        return identities
    
    # ==================== Feedback Operations ====================
    
    async def save_sport_feedback(
        self,
        user_id: str,
        feedback: SportFeedback
    ):
        """Save user feedback on a sport"""
        async with self._get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO sport_feedback (
                    user_id, sport_label, tried, enjoyed, rating, why, feedback_date
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                user_id,
                feedback.sport_label,
                feedback.tried,
                feedback.enjoyed,
                feedback.rating,
                feedback.why,
                feedback.feedback_date
            )
        
        # Update user progress
        if feedback.tried:
            await self._increment_sports_tried(user_id)
        
        logger.info(f"Feedback saved for user {user_id}: {feedback.sport_label}")
    
    async def _load_sport_feedback(
        self,
        conn: Connection,
        user_id: str
    ) -> List[SportFeedback]:
        """Load user's sport feedback"""
        rows = await conn.fetch(
            """
            SELECT * FROM sport_feedback 
            WHERE user_id = $1 
            ORDER BY feedback_date DESC
            """,
            user_id
        )
        
        feedbacks = []
        for row in rows:
            try:
                feedbacks.append(SportFeedback(**dict(row)))
            except Exception as e:
                logger.error(f"Failed to parse feedback: {e}")
        
        return feedbacks
    
    # ==================== Progress Tracking ====================
    
    async def update_progress(
        self,
        user_id: str,
        progress_updates: Dict[str, Any]
    ):
        """Update user progress metrics"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Merge updates
        current_progress = user.progress.dict()
        current_progress.update(progress_updates)
        current_progress['last_activity'] = datetime.utcnow()
        
        await self.update_user(user_id, {'progress': current_progress})
    
    async def _increment_sports_tried(self, user_id: str):
        """Increment sports tried counter"""
        user = await self.get_user_by_id(user_id)
        if user:
            await self.update_progress(user_id, {
                'sports_tried': user.progress.sports_tried + 1
            })
    
    async def log_activity(
        self,
        user_id: str,
        activity_type: str,
        activity_data: Dict[str, Any] = None,
        session_id: Optional[str] = None
    ):
        """Log user activity"""
        async with self._get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO user_activities (
                    user_id, activity_type, activity_data, session_id, timestamp
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                user_id,
                activity_type,
                json.dumps(activity_data or {}),
                session_id,
                datetime.utcnow()
            )
    
    # ==================== Analytics ====================
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return {}
        
        async with self._get_connection() as conn:
            # Get activity counts
            activity_counts = await conn.fetch(
                """
                SELECT activity_type, COUNT(*) as count
                FROM user_activities
                WHERE user_id = $1
                GROUP BY activity_type
                """,
                user_id
            )
            
            # Get feedback summary
            feedback_summary = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_feedback,
                    SUM(CASE WHEN tried THEN 1 ELSE 0 END) as tried_count,
                    AVG(rating) as avg_rating
                FROM sport_feedback
                WHERE user_id = $1
                """,
                user_id
            )
        
        return {
            'user_id': user_id,
            'account_age_days': (datetime.utcnow() - user.created_at).days,
            'progress': user.progress.dict(),
            'activity_counts': {row['activity_type']: row['count'] for row in activity_counts},
            'feedback_summary': dict(feedback_summary) if feedback_summary else {},
            'subscription_tier': user.subscription_tier.value,
            'is_active_subscriber': user.is_active_subscriber
        }
    
    # ==================== Collaborative Filtering Helpers ====================
    
    async def get_similar_users(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[str]:
        """Find similar users based on Layer-Z profile and feedback"""
        user = await self.get_user_by_id(user_id)
        if not user or not user.layer_z_profile:
            return []
        
        # This is a simplified version - should use proper vector similarity
        async with self._get_connection() as conn:
            # Find users who tried similar sports
            similar_users = await conn.fetch(
                """
                SELECT DISTINCT sf2.user_id, COUNT(*) as common_sports
                FROM sport_feedback sf1
                JOIN sport_feedback sf2 ON sf1.sport_label = sf2.sport_label
                WHERE sf1.user_id = $1 AND sf2.user_id != $1 AND sf1.tried AND sf2.tried
                GROUP BY sf2.user_id
                ORDER BY common_sports DESC
                LIMIT $2
                """,
                user_id, limit
            )
        
        return [row['user_id'] for row in similar_users]
    
    # ==================== Utility Methods ====================
    
    def _generate_user_id(self) -> str:
        """Generate unique user ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self._get_connection() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# ==================== Global Database Instance ====================

_db_manager: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def init_db():
    """Initialize database connection"""
    db = get_db()
    await db.initialize()


async def close_db():
    """Close database connection"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
