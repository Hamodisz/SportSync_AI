# -*- coding: utf-8 -*-
"""
users/auth.py
------------
Authentication and authorization system.
Password hashing, JWT tokens, session management.

© Sports Sync AI - 2025
"""

from __future__ import annotations
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import bcrypt
import jwt
from pydantic import BaseModel, EmailStr

from users.database import get_db
from users.models import UserProfile, AccountStatus


# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days


class AuthTokens(BaseModel):
    """Authentication tokens"""
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    user_id: str


class AuthenticationError(Exception):
    """Authentication failed"""
    pass


class AuthorizationError(Exception):
    """Authorization failed (insufficient permissions)"""
    pass


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )


def create_access_token(
    user_id: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> AuthTokens:
    """Create JWT access token"""
    expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        'user_id': user_id,
        'exp': expires_at,
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return AuthTokens(
        access_token=token,
        expires_at=expires_at,
        user_id=user_id
    )


def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify JWT access token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check expiration
        if datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
            raise AuthenticationError("Token expired")
        
        return payload
    
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {e}")


async def register_user(
    email: EmailStr,
    name: str,
    password: str,
    language: str = "العربية"
) -> tuple[UserProfile, AuthTokens]:
    """Register new user and return user + tokens"""
    
    # Validate password strength
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    # Hash password
    password_hash = hash_password(password)
    
    # Create user
    db = get_db()
    user = await db.create_user(
        email=email,
        name=name,
        password_hash=password_hash,
        language=language
    )
    
    # Generate tokens
    tokens = create_access_token(user.id)
    
    # Log activity
    await db.log_activity(
        user_id=user.id,
        activity_type='user_registered'
    )
    
    return user, tokens


async def login_user(
    email: EmailStr,
    password: str
) -> tuple[UserProfile, AuthTokens]:
    """Login user and return user + tokens"""
    
    db = get_db()
    
    # Get user
    user = await db.get_user_by_email(email)
    if not user:
        raise AuthenticationError("Invalid email or password")
    
    # Check account status
    if user.account_status != AccountStatus.ACTIVE:
        raise AuthenticationError(f"Account is {user.account_status.value}")
    
    # Verify password
    # Get password hash from secure table
    async with db._get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT password_hash FROM user_credentials WHERE user_id = $1",
            user.id
        )
        if not row:
            raise AuthenticationError("Invalid email or password")
        
        password_hash = row['password_hash']
    
    if not verify_password(password, password_hash):
        raise AuthenticationError("Invalid email or password")
    
    # Update last login
    await db.update_user(user.id, {'last_login': datetime.utcnow()})
    
    # Generate tokens
    tokens = create_access_token(user.id)
    
    # Log activity
    await db.log_activity(
        user_id=user.id,
        activity_type='user_logged_in'
    )
    
    return user, tokens


async def get_current_user(token: str) -> UserProfile:
    """Get current user from access token"""
    
    # Verify token
    payload = verify_access_token(token)
    user_id = payload.get('user_id')
    
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # Get user
    db = get_db()
    user = await db.get_user_by_id(user_id)
    
    if not user:
        raise AuthenticationError("User not found")
    
    if user.account_status != AccountStatus.ACTIVE:
        raise AuthenticationError(f"Account is {user.account_status.value}")
    
    return user


async def refresh_access_token(old_token: str) -> AuthTokens:
    """Refresh access token (if still valid)"""
    
    payload = verify_access_token(old_token)
    user_id = payload.get('user_id')
    
    # Create new token
    return create_access_token(user_id)


async def logout_user(token: str):
    """Logout user (in practice, client should discard token)"""
    
    # Get user
    user = await get_current_user(token)
    
    # Log activity
    db = get_db()
    await db.log_activity(
        user_id=user.id,
        activity_type='user_logged_out'
    )


async def change_password(
    user_id: str,
    old_password: str,
    new_password: str
):
    """Change user password"""
    
    db = get_db()
    
    # Verify old password
    async with db._get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT password_hash FROM user_credentials WHERE user_id = $1",
            user_id
        )
        if not row:
            raise AuthenticationError("User not found")
        
        password_hash = row['password_hash']
    
    if not verify_password(old_password, password_hash):
        raise AuthenticationError("Incorrect old password")
    
    # Validate new password
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    # Hash and update
    new_hash = hash_password(new_password)
    
    async with db._get_connection() as conn:
        await conn.execute(
            "UPDATE user_credentials SET password_hash = $1 WHERE user_id = $2",
            new_hash, user_id
        )
    
    # Log activity
    await db.log_activity(
        user_id=user_id,
        activity_type='password_changed'
    )


async def reset_password_request(email: EmailStr) -> str:
    """Request password reset (generate reset token)"""
    
    db = get_db()
    user = await db.get_user_by_email(email)
    
    if not user:
        # Don't reveal if email exists
        return "reset_token_placeholder"
    
    # Generate reset token (expires in 1 hour)
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Store reset token
    async with db._get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO password_reset_tokens (user_id, token, expires_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE 
            SET token = $2, expires_at = $3
            """,
            user.id, reset_token, expires_at
        )
    
    # TODO: Send email with reset link
    # send_password_reset_email(user.email, reset_token)
    
    return reset_token


async def reset_password_confirm(
    reset_token: str,
    new_password: str
):
    """Confirm password reset with token"""
    
    db = get_db()
    
    # Validate token
    async with db._get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT user_id FROM password_reset_tokens
            WHERE token = $1 AND expires_at > $2
            """,
            reset_token, datetime.utcnow()
        )
        
        if not row:
            raise AuthenticationError("Invalid or expired reset token")
        
        user_id = row['user_id']
        
        # Validate new password
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Hash and update
        new_hash = hash_password(new_password)
        
        await conn.execute(
            "UPDATE user_credentials SET password_hash = $1 WHERE user_id = $2",
            new_hash, user_id
        )
        
        # Delete used reset token
        await conn.execute(
            "DELETE FROM password_reset_tokens WHERE user_id = $1",
            user_id
        )
    
    # Log activity
    await db.log_activity(
        user_id=user_id,
        activity_type='password_reset'
    )


# ==================== Authorization Helpers ====================

def require_subscription(tier: str = "pro"):
    """Decorator to require specific subscription tier"""
    def decorator(func):
        async def wrapper(user: UserProfile, *args, **kwargs):
            if not user.is_active_subscriber:
                raise AuthorizationError("Active subscription required")
            
            tier_hierarchy = {
                'free': 0,
                'pro': 1,
                'premium': 2,
                'enterprise': 3
            }
            
            user_tier = tier_hierarchy.get(user.subscription_tier.value, 0)
            required_tier = tier_hierarchy.get(tier, 0)
            
            if user_tier < required_tier:
                raise AuthorizationError(f"{tier.capitalize()} subscription required")
            
            return await func(user, *args, **kwargs)
        return wrapper
    return decorator
