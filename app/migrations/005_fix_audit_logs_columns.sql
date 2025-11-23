-- Add missing columns to audit_logs table if they don't exist
-- SQLite compatible (will fail silently if columns exist)

-- Add ip column
ALTER TABLE audit_logs ADD COLUMN ip TEXT;

-- Add user_agent column
ALTER TABLE audit_logs ADD COLUMN user_agent TEXT;

-- Add status column
ALTER TABLE audit_logs ADD COLUMN status TEXT DEFAULT 'success';

-- Add resource column
ALTER TABLE audit_logs ADD COLUMN resource TEXT;

-- Add meta column
ALTER TABLE audit_logs ADD COLUMN meta TEXT DEFAULT '{}';

