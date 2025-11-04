# -*- coding: utf-8 -*-
"""
users/__init__.py
----------------
User management system for SportSync AI.

© Sports Sync AI - 2025
"""

from users.models import (
    UserProfile,
    SportIdentityCard,
    SportFeedback,
    ProgressMetrics,
    UserActivity,
    AccountStatus,
    SubscriptionTier,
    UserRegistrationRequest,
    UserLoginRequest,
    UserUpdateRequest,
    SportFeedbackRequest,
    UserProgressResponse
)

from users.database import (
    DatabaseManager,
    get_db,
    init_db,
    close_db
)

from users.auth import (
    AuthTokens,
    AuthenticationError,
    AuthorizationError,
    register_user,
    login_user,
    get_current_user,
    logout_user,
    change_password,
    reset_password_request,
    reset_password_confirm,
    require_subscription
)

__all__ = [
    # Models
    'UserProfile',
    'SportIdentityCard',
    'SportFeedback',
    'ProgressMetrics',
    'UserActivity',
    'AccountStatus',
    'SubscriptionTier',
    'UserRegistrationRequest',
    'UserLoginRequest',
    'UserUpdateRequest',
    'SportFeedbackRequest',
    'UserProgressResponse',
    
    # Database
    'DatabaseManager',
    'get_db',
    'init_db',
    'close_db',
    
    # Auth
    'AuthTokens',
    'AuthenticationError',
    'AuthorizationError',
    'register_user',
    'login_user',
    'get_current_user',
    'logout_user',
    'change_password',
    'reset_password_request',
    'reset_password_confirm',
    'require_subscription',
]
