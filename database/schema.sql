-- ========================================
-- SportSync AI - Supabase Database Schema
-- Collaborative Filtering & User Analytics
-- ========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- 1. Users Table
-- ========================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_hash TEXT UNIQUE NOT NULL,  -- Anonymous user identifier
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    language TEXT DEFAULT 'ar',
    country TEXT DEFAULT 'SA',
    total_sessions INTEGER DEFAULT 1,
    last_session_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_users_hash ON users(user_hash);
CREATE INDEX idx_users_created ON users(created_at DESC);

-- ========================================
-- 2. Quiz Responses Table
-- ========================================
CREATE TABLE IF NOT EXISTS quiz_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL DEFAULT uuid_generate_v4(),
    question_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    answer_value TEXT NOT NULL,
    answer_index INTEGER,
    category TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_quiz_user ON quiz_responses(user_id);
CREATE INDEX idx_quiz_session ON quiz_responses(session_id);
CREATE INDEX idx_quiz_question ON quiz_responses(question_id);
CREATE INDEX idx_quiz_category ON quiz_responses(category);

-- ========================================
-- 3. User Traits (Psychological Profile)
-- ========================================
CREATE TABLE IF NOT EXISTS user_traits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    
    -- Identity Scores (0-10)
    warrior DECIMAL(4,2) DEFAULT 0,
    explorer DECIMAL(4,2) DEFAULT 0,
    builder DECIMAL(4,2) DEFAULT 0,
    connector DECIMAL(4,2) DEFAULT 0,
    
    -- Personality Traits (0-10)
    extroversion DECIMAL(4,2) DEFAULT 0,
    openness DECIMAL(4,2) DEFAULT 0,
    competitiveness DECIMAL(4,2) DEFAULT 0,
    risk_tolerance DECIMAL(4,2) DEFAULT 0,
    discipline DECIMAL(4,2) DEFAULT 0,
    social_preference DECIMAL(4,2) DEFAULT 0,
    energy_level DECIMAL(4,2) DEFAULT 0,
    stress_tolerance DECIMAL(4,2) DEFAULT 0,
    achievement_drive DECIMAL(4,2) DEFAULT 0,
    creativity DECIMAL(4,2) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_traits_user ON user_traits(user_id);
CREATE INDEX idx_traits_session ON user_traits(session_id);

-- ========================================
-- 4. Recommendations Table
-- ========================================
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    rank INTEGER NOT NULL,  -- 1, 2, 3
    
    sport_label TEXT NOT NULL,
    sport_category TEXT,
    match_percentage INTEGER,
    
    -- Recommendation details (JSONB for flexibility)
    details JSONB NOT NULL,
    
    -- User interaction
    was_shown BOOLEAN DEFAULT TRUE,
    clicked BOOLEAN DEFAULT FALSE,
    liked BOOLEAN DEFAULT NULL,  -- NULL, TRUE, FALSE
    interaction_time TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_rec_user ON recommendations(user_id);
CREATE INDEX idx_rec_session ON recommendations(session_id);
CREATE INDEX idx_rec_sport ON recommendations(sport_label);
CREATE INDEX idx_rec_liked ON recommendations(liked) WHERE liked IS NOT NULL;

-- ========================================
-- 5. Sport Ratings (for Collaborative Filtering)
-- ========================================
CREATE TABLE IF NOT EXISTS sport_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    sport_label TEXT NOT NULL,
    
    -- Implicit rating (derived from interactions)
    rating DECIMAL(3,2) NOT NULL,  -- 0.0 to 5.0
    confidence DECIMAL(3,2) DEFAULT 1.0,  -- How confident we are
    
    -- Interaction signals
    was_recommended BOOLEAN DEFAULT FALSE,
    was_clicked BOOLEAN DEFAULT FALSE,
    was_liked BOOLEAN DEFAULT FALSE,
    time_spent_seconds INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, sport_label)
);

-- Indexes
CREATE INDEX idx_rating_user ON sport_ratings(user_id);
CREATE INDEX idx_rating_sport ON sport_ratings(sport_label);
CREATE INDEX idx_rating_value ON sport_ratings(rating DESC);

-- ========================================
-- 6. Similar Users (Precomputed)
-- ========================================
CREATE TABLE IF NOT EXISTS similar_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    similar_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5,4) NOT NULL,  -- 0.0 to 1.0
    
    -- What makes them similar
    shared_traits JSONB,
    
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, similar_user_id)
);

-- Indexes
CREATE INDEX idx_similar_user ON similar_users(user_id);
CREATE INDEX idx_similar_score ON similar_users(similarity_score DESC);

-- ========================================
-- 7. Analytics Events
-- ========================================
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID,
    event_type TEXT NOT NULL,  -- quiz_started, quiz_completed, recommendation_viewed, etc.
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_events_user ON analytics_events(user_id);
CREATE INDEX idx_events_type ON analytics_events(event_type);
CREATE INDEX idx_events_created ON analytics_events(created_at DESC);

-- ========================================
-- Views for Analytics
-- ========================================

-- Popular sports view
CREATE OR REPLACE VIEW popular_sports AS
SELECT 
    sport_label,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(rating) as avg_rating,
    COUNT(*) as total_ratings,
    SUM(CASE WHEN was_liked THEN 1 ELSE 0 END) as total_likes
FROM sport_ratings
GROUP BY sport_label
ORDER BY unique_users DESC, avg_rating DESC;

-- User engagement view
CREATE OR REPLACE VIEW user_engagement AS
SELECT 
    u.id as user_id,
    u.user_hash,
    u.total_sessions,
    u.language,
    COUNT(DISTINCT r.id) as total_recommendations,
    COUNT(DISTINCT sr.id) as total_ratings,
    AVG(sr.rating) as avg_rating_given,
    u.created_at as first_seen,
    u.last_session_at
FROM users u
LEFT JOIN recommendations r ON u.id = r.user_id
LEFT JOIN sport_ratings sr ON u.id = sr.user_id
GROUP BY u.id, u.user_hash, u.total_sessions, u.language, u.created_at, u.last_session_at;

-- ========================================
-- Functions
-- ========================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for sport_ratings table
CREATE TRIGGER update_ratings_updated_at BEFORE UPDATE ON sport_ratings
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- Row Level Security (RLS) Policies
-- ========================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_traits ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE sport_ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE similar_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (for backend API)
CREATE POLICY "Service role has full access to users" ON users
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to quiz_responses" ON quiz_responses
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to user_traits" ON user_traits
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to recommendations" ON recommendations
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to sport_ratings" ON sport_ratings
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to similar_users" ON similar_users
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to analytics_events" ON analytics_events
FOR ALL USING (auth.role() = 'service_role');

-- ========================================
-- Sample Data for Testing
-- ========================================

-- Note: Run this separately after initial setup
-- INSERT INTO users (user_hash, language) VALUES 
-- ('test_user_1', 'ar'),
-- ('test_user_2', 'en');
