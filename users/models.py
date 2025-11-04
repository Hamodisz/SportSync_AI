# -*- coding: utf-8 -*-
"""
users/models.py
--------------
Pydantic models for user management system.
Complete user profile with sport identity, progress tracking, and preferences.

© Sports Sync AI - 2025
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class AccountStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SubscriptionTier(str, Enum):
    """Subscription tiers for monetization"""
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SportIdentityCard(BaseModel):
    """Single sport recommendation card"""
    sport_label: str
    category: str  # realistic, alternative, creative
    what_it_looks_like: str
    inner_sensation: str
    why_you: str
    first_week: str
    core_skills: List[str] = []
    mode: str = "Solo/Team"
    variant_vr: str
    variant_no_vr: str
    difficulty: int = Field(ge=1, le=5)
    source: str = "KB"  # KB, HYBRID, LLM
    recommended_at: datetime = Field(default_factory=datetime.utcnow)


class SportFeedback(BaseModel):
    """User feedback on a sport recommendation"""
    sport_label: str
    tried: bool = False  # Did they actually try it?
    enjoyed: Optional[bool] = None  # Did they like it?
    continuing: bool = False  # Will they continue?
    rating: Optional[int] = Field(None, ge=1, le=5)  # 1-5 stars
    why: Optional[str] = None  # Open-ended feedback
    tried_date: Optional[date] = None
    feedback_date: datetime = Field(default_factory=datetime.utcnow)


class ProgressMetrics(BaseModel):
    """User progress tracking metrics"""
    days_active: int = 0
    total_logins: int = 0
    sports_discovered: int = 0
    sports_tried: int = 0
    sports_mastered: int = 0  # Sports with 30+ days of practice
    current_streak: int = 0  # Days in a row with activity
    longest_streak: int = 0
    total_workouts_logged: int = 0
    total_minutes_exercised: int = 0
    badges_earned: List[str] = []
    level: int = 1  # User level (1-100)
    experience_points: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)


class LayerZProfile(BaseModel):
    """Layer-Z psychological profile"""
    z_scores: Dict[str, float] = {}  # 7 axes: -1 to +1
    z_drivers: List[str] = []  # Interpreted motivations
    profile_version: str = "1.0"
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)


class UserPreferences(BaseModel):
    """User preferences and settings"""
    language: str = "العربية"  # or "English"
    notification_enabled: bool = True
    email_notifications: bool = True
    push_notifications: bool = True
    public_profile: bool = False  # Social features
    share_progress: bool = False
    theme: str = "auto"  # dark, light, auto
    preferred_sport_categories: List[str] = []
    avoided_sport_types: List[str] = []  # e.g., ["high-risk", "water-based"]


class UserProfile(BaseModel):
    """Complete user profile"""
    # Basic Info
    id: str = Field(..., description="Unique user ID (UUID)")
    email: EmailStr
    name: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    location: Optional[str] = None  # City/Country
    
    # Account
    account_status: AccountStatus = AccountStatus.ACTIVE
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    subscription_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)
    
    # Sport Identity
    sport_identities: List[SportIdentityCard] = []  # All recommendations received
    current_sports: List[str] = []  # Sports currently practicing
    sport_feedback: List[SportFeedback] = []
    
    # Progress & Engagement
    progress: ProgressMetrics = Field(default_factory=ProgressMetrics)
    layer_z_profile: Optional[LayerZProfile] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # Social
    followers: List[str] = []  # User IDs
    following: List[str] = []  # User IDs
    
    # Metadata
    metadata: Dict[str, Any] = {}  # Flexible field for extensions
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        if v:
            age = (datetime.now().date() - v).days / 365.25
            if age < 13:
                raise ValueError("User must be at least 13 years old")
            if age > 120:
                raise ValueError("Invalid birth date")
        return v
    
    @property
    def age(self) -> Optional[int]:
        """Calculate user age"""
        if self.date_of_birth:
            return int((datetime.now().date() - self.date_of_birth).days / 365.25)
        return None
    
    @property
    def is_pro(self) -> bool:
        """Check if user has pro subscription"""
        return self.subscription_tier in [SubscriptionTier.PRO, SubscriptionTier.PREMIUM]
    
    @property
    def is_active_subscriber(self) -> bool:
        """Check if subscription is active"""
        if self.subscription_tier == SubscriptionTier.FREE:
            return False
        if self.subscription_expires_at:
            return datetime.utcnow() < self.subscription_expires_at
        return True


class UserActivity(BaseModel):
    """Track user activities for analytics"""
    user_id: str
    activity_type: str  # login, recommendation_viewed, sport_tried, feedback_given, etc.
    activity_data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None


class UserSession(BaseModel):
    """User session tracking"""
    session_id: str
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    activities: List[UserActivity] = []


# ==================== Response Models ====================

class UserRegistrationRequest(BaseModel):
    """Request to register new user"""
    email: EmailStr
    name: str
    password: str = Field(..., min_length=8)
    language: str = "العربية"
    agree_to_terms: bool = True
    
    @validator('agree_to_terms')
    def must_agree_to_terms(cls, v):
        if not v:
            raise ValueError("Must agree to terms and conditions")
        return v


class UserLoginRequest(BaseModel):
    """Request to login"""
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    """Request to update user profile"""
    name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    preferences: Optional[UserPreferences] = None


class SportFeedbackRequest(BaseModel):
    """Request to submit sport feedback"""
    sport_label: str
    tried: bool = False
    enjoyed: Optional[bool] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    why: Optional[str] = None


class UserProgressResponse(BaseModel):
    """Response with user progress data"""
    user_id: str
    progress: ProgressMetrics
    recent_activities: List[UserActivity] = []
    achievements: List[str] = []
    next_milestones: List[Dict[str, Any]] = []


# ==================== Database Schema Hints ====================
"""
PostgreSQL Table Schema:

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    date_of_birth DATE,
    gender VARCHAR(20),
    location VARCHAR(255),
    account_status VARCHAR(20) DEFAULT 'active',
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP DEFAULT NOW(),
    layer_z_profile JSONB,
    preferences JSONB DEFAULT '{}',
    progress JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    CONSTRAINT check_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription ON users(subscription_tier, subscription_expires_at);

CREATE TABLE sport_identities (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    sport_label VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    card_data JSONB NOT NULL,
    recommended_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_sport_identities_user ON sport_identities(user_id);

CREATE TABLE sport_feedback (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    sport_label VARCHAR(255) NOT NULL,
    tried BOOLEAN DEFAULT false,
    enjoyed BOOLEAN,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    why TEXT,
    feedback_date TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sport_feedback_user ON sport_feedback(user_id);
CREATE INDEX idx_sport_feedback_sport ON sport_feedback(sport_label);

CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    activity_type VARCHAR(100) NOT NULL,
    activity_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_activities_user ON user_activities(user_id, timestamp);
CREATE INDEX idx_user_activities_type ON user_activities(activity_type);

CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ip_address VARCHAR(50),
    user_agent TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP
);

CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
"""
