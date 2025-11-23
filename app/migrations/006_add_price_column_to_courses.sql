-- Migration: Add missing columns to users, courses, blogs, and sessions tables
-- SQLite-compatible version (no procedural blocks)
-- Note: ALTER TABLE ADD COLUMN will fail silently if column already exists in SQLite

-- ===== USERS TABLE =====
ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN two_factor_secret TEXT;
ALTER TABLE users ADD COLUMN profile_picture TEXT;
ALTER TABLE users ADD COLUMN oauth_provider TEXT;
ALTER TABLE users ADD COLUMN oauth_provider_id TEXT;
ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- ===== SESSIONS TABLE =====
-- Note: SQLite doesn't support RENAME COLUMN in older versions, 
-- and we can't conditionally add columns, so these might fail if they exist
ALTER TABLE sessions ADD COLUMN refresh_token TEXT UNIQUE;
ALTER TABLE sessions ADD COLUMN ip TEXT;
ALTER TABLE sessions ADD COLUMN device_info TEXT;
ALTER TABLE sessions ADD COLUMN last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- ===== COURSES TABLE =====
ALTER TABLE courses ADD COLUMN price REAL;
ALTER TABLE courses ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- ===== BLOGS TABLE =====
ALTER TABLE blogs ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
