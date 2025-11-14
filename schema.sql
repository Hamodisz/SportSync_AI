-- SportSync AI Database Schema
-- PostgreSQL 15+
-- Created: 2025-11-12

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- USERS TABLE
-- =====================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    language VARCHAR(10) NOT NULL CHECK (language IN ('ar', 'en')),
    profile JSONB,
    metadata JSONB,
    CONSTRAINT users_language_check CHECK (language IN ('ar', 'en'))
);

COMMENT ON TABLE users IS 'المستخدمون الأساسيون';
COMMENT ON COLUMN users.profile IS 'بيانات التحليل النفسي (141 طبقة + Layer-Z)';
COMMENT ON COLUMN users.metadata IS 'بيانات إضافية (device, location, etc)';

-- =====================================================
-- USER_SESSIONS TABLE
-- =====================================================
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_data JSONB NOT NULL,
    answers JSONB,
    z_scores JSONB,
    systems_analysis JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    completed BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE user_sessions IS 'جلسات المستخدمين';
COMMENT ON COLUMN user_sessions.answers IS 'إجابات الـ 20 سؤال';
COMMENT ON COLUMN user_sessions.z_scores IS 'Z-Axes (Calm/Solo/Tech)';
COMMENT ON COLUMN user_sessions.systems_analysis IS 'تحليل الأنظمة الصامتة (15)';

-- =====================================================
-- RECOMMENDATIONS TABLE
-- =====================================================
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
    sport_name VARCHAR(255) NOT NULL,
    sport_label VARCHAR(255) NOT NULL,
    match_score FLOAT CHECK (match_score >= 0 AND match_score <= 1),
    z_alignment JSONB,
    card_data JSONB,
    variant VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE recommendations IS 'التوصيات الرياضية';
COMMENT ON COLUMN recommendations.z_alignment IS 'توافق Z-Axes';
COMMENT ON COLUMN recommendations.card_data IS 'Sport Identity Card كامل';
COMMENT ON COLUMN recommendations.variant IS 'VR أو No-VR';

-- =====================================================
-- BLACKLIST TABLE
-- =====================================================
CREATE TABLE blacklist (
    id SERIAL PRIMARY KEY,
    sport_label VARCHAR(255) UNIQUE NOT NULL,
    reason VARCHAR(255),
    added_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE blacklist IS 'قائمة الرياضات المستبعدة لمنع التكرار';

-- =====================================================
-- ANALYTICS_EVENTS TABLE
-- =====================================================
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_name VARCHAR(100) NOT NULL,
    event_properties JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE analytics_events IS 'أحداث التحليلات (Activation, Retention, etc)';

-- =====================================================
-- AB_EXPERIMENTS TABLE
-- =====================================================
CREATE TABLE ab_experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_name VARCHAR(100) UNIQUE NOT NULL,
    variant_a JSONB NOT NULL,
    variant_b JSONB NOT NULL,
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE ab_experiments IS 'تجارب A/B Testing';

-- =====================================================
-- USER_AB_ASSIGNMENTS TABLE
-- =====================================================
CREATE TABLE user_ab_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    experiment_id UUID REFERENCES ab_experiments(id) ON DELETE CASCADE,
    variant VARCHAR(10) CHECK (variant IN ('A', 'B')),
    assigned_at TIMESTAMP DEFAULT NOW(),
    converted BOOLEAN DEFAULT FALSE,
    converted_at TIMESTAMP,
    UNIQUE(user_id, experiment_id)
);

COMMENT ON TABLE user_ab_assignments IS 'توزيع المستخدمين على التجارب';

-- =====================================================
-- INDEXES للأداء
-- =====================================================

-- Users indexes
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_language ON users(language);

-- Sessions indexes
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_created_at ON user_sessions(created_at);
CREATE INDEX idx_sessions_completed ON user_sessions(completed);

-- Recommendations indexes
CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX idx_recommendations_session_id ON recommendations(session_id);
CREATE INDEX idx_recommendations_sport_label ON recommendations(sport_label);
CREATE INDEX idx_recommendations_created_at ON recommendations(created_at);
CREATE INDEX idx_recommendations_match_score ON recommendations(match_score DESC);

-- Blacklist indexes
CREATE INDEX idx_blacklist_label ON blacklist(sport_label);

-- Analytics indexes
CREATE INDEX idx_analytics_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_event_name ON analytics_events(event_name);
CREATE INDEX idx_analytics_created_at ON analytics_events(created_at);

-- A/B Testing indexes
CREATE INDEX idx_ab_experiments_name ON ab_experiments(experiment_name);
CREATE INDEX idx_ab_experiments_active ON ab_experiments(is_active);
CREATE INDEX idx_ab_assignments_user ON user_ab_assignments(user_id);
CREATE INDEX idx_ab_assignments_experiment ON user_ab_assignments(experiment_id);

-- =====================================================
-- FUNCTIONS للمساعدة
-- =====================================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger: Auto-update updated_at on users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function: Calculate 7-day retention
CREATE OR REPLACE FUNCTION calculate_7day_retention(user_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    first_seen TIMESTAMP;
    last_seen TIMESTAMP;
    days_diff INTEGER;
BEGIN
    SELECT MIN(created_at), MAX(created_at) INTO first_seen, last_seen
    FROM analytics_events
    WHERE user_id = user_uuid;
    
    IF first_seen IS NULL OR last_seen IS NULL THEN
        RETURN FALSE;
    END IF;
    
    days_diff := EXTRACT(DAY FROM (last_seen - first_seen));
    RETURN days_diff <= 7;
END;
$$ LANGUAGE plpgsql;

-- Function: Calculate activation rate
CREATE OR REPLACE FUNCTION calculate_activation_rate(
    start_date TIMESTAMP,
    end_date TIMESTAMP
)
RETURNS FLOAT AS $$
DECLARE
    total_users INTEGER;
    activated_users INTEGER;
BEGIN
    -- Count users who completed sessions
    SELECT COUNT(DISTINCT user_id) INTO total_users
    FROM user_sessions
    WHERE created_at BETWEEN start_date AND end_date
    AND completed = TRUE;
    
    -- Count users who got recommendations
    SELECT COUNT(DISTINCT user_id) INTO activated_users
    FROM recommendations
    WHERE created_at BETWEEN start_date AND end_date;
    
    IF total_users = 0 THEN
        RETURN 0;
    END IF;
    
    RETURN (activated_users::FLOAT / total_users::FLOAT) * 100;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS للتحليلات
-- =====================================================

-- View: User activity summary
CREATE VIEW user_activity_summary AS
SELECT 
    u.id,
    u.created_at,
    u.language,
    COUNT(DISTINCT us.id) as total_sessions,
    COUNT(DISTINCT r.id) as total_recommendations,
    MAX(us.last_active) as last_active
FROM users u
LEFT JOIN user_sessions us ON u.id = us.user_id
LEFT JOIN recommendations r ON u.id = r.user_id
GROUP BY u.id;

COMMENT ON VIEW user_activity_summary IS 'ملخص نشاط المستخدمين';

-- View: Daily stats
CREATE VIEW daily_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as daily_users,
    COUNT(*) as total_sessions,
    SUM(CASE WHEN completed THEN 1 ELSE 0 END) as completed_sessions
FROM user_sessions
GROUP BY DATE(created_at)
ORDER BY date DESC;

COMMENT ON VIEW daily_stats IS 'إحصائيات يومية';

-- View: Top sports
CREATE VIEW top_sports AS
SELECT 
    sport_label,
    sport_name,
    COUNT(*) as recommendation_count,
    AVG(match_score) as avg_match_score
FROM recommendations
GROUP BY sport_label, sport_name
ORDER BY recommendation_count DESC;

COMMENT ON VIEW top_sports IS 'أكثر الرياضات توصية';

-- =====================================================
-- SEED DATA (اختياري)
-- =====================================================

-- إضافة بعض الرياضات للـ blacklist (مثال)
-- INSERT INTO blacklist (sport_label, reason) VALUES
-- ('generic_sport', 'Too generic'),
-- ('deprecated_sport', 'Removed from catalog');

-- =====================================================
-- GRANTS (للأمان)
-- =====================================================

-- Create read-only user for analytics
-- CREATE USER sportsync_readonly WITH PASSWORD 'your_password_here';
-- GRANT CONNECT ON DATABASE sportsync TO sportsync_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO sportsync_readonly;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO sportsync_readonly;

-- =====================================================
-- END OF SCHEMA
-- =====================================================

-- To execute this schema:
-- psql sportsync < schema.sql
