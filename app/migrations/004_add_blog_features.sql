-- Migration 004: Add blog features (tags, categories, scheduled publishing)

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create blog_tags junction table
CREATE TABLE IF NOT EXISTS blog_tags (
    blog_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (blog_id, tag_id),
    FOREIGN KEY (blog_id) REFERENCES blogs (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
);

-- Add new columns to blogs table (SQLite doesn't support adding multiple columns in one statement)
-- First, check if columns exist by trying to add them
-- SQLite will skip if the column already exists when using IF NOT EXISTS pattern

-- We need to check if the columns exist before adding them
-- Since SQLite doesn't have IF NOT EXISTS for ALTER TABLE, we'll use a workaround

-- Add publish_at column
ALTER TABLE blogs ADD COLUMN publish_at TIMESTAMP NULL;

-- Add tags column
ALTER TABLE blogs ADD COLUMN tags TEXT DEFAULT '[]';

-- Insert default categories
INSERT OR IGNORE INTO categories (name, slug, description) VALUES 
('Market Analysis', 'market-analysis', 'Analysis of market trends and movements'),
('Investment Tips', 'investment-tips', 'Tips and strategies for investments'),
('Trading Strategies', 'trading-strategies', 'Various trading strategies and techniques'),
('Financial News', 'financial-news', 'Latest news in finance and economics'),
('Industry Insights', 'industry-insights', 'Insights into various industries');
