-- Add missing columns to blogs table in PostgreSQL

-- Check and add columns one by one
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS slug VARCHAR(255) UNIQUE;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS image_alt TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS featured BOOLEAN DEFAULT FALSE;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS meta_title TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS meta_description TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS canonical_url TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS og_title TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS og_description TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS og_image_url TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS og_image_alt TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS reading_time FLOAT DEFAULT 0.0;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS categories TEXT;

-- Generate slugs for existing blogs that don't have one
UPDATE blogs 
SET slug = LOWER(REGEXP_REPLACE(REGEXP_REPLACE(title, '[^a-zA-Z0-9\s-]', '', 'g'), '\s+', '-', 'g'))
WHERE slug IS NULL OR slug = '';
