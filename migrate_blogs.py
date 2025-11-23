"""
Migration script to add missing columns to blogs table
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from app.services.d1_service import database

def migrate():
    database.connect()
    
    print("Starting migration to add missing blog columns...")
    
    # Get current columns
    current_cols = database.fetch_all('PRAGMA table_info(blogs)')
    current_col_names = [col['name'] for col in current_cols]
    print(f"Current columns: {current_col_names}")
    
    migrations = [
        ("slug", "ALTER TABLE blogs ADD COLUMN slug TEXT"),
        ("image_alt", "ALTER TABLE blogs ADD COLUMN image_alt TEXT"),
        ("featured", "ALTER TABLE blogs ADD COLUMN featured BOOLEAN DEFAULT FALSE"),
        ("meta_title", "ALTER TABLE blogs ADD COLUMN meta_title TEXT"),
        ("meta_description", "ALTER TABLE blogs ADD COLUMN meta_description TEXT"),
        ("canonical_url", "ALTER TABLE blogs ADD COLUMN canonical_url TEXT"),
        ("og_title", "ALTER TABLE blogs ADD COLUMN og_title TEXT"),
        ("og_description", "ALTER TABLE blogs ADD COLUMN og_description TEXT"),
        ("og_image_url", "ALTER TABLE blogs ADD COLUMN og_image_url TEXT"),
        ("og_image_alt", "ALTER TABLE blogs ADD COLUMN og_image_alt TEXT"),
        ("word_count", "ALTER TABLE blogs ADD COLUMN word_count INTEGER DEFAULT 0"),
        ("reading_time", "ALTER TABLE blogs ADD COLUMN reading_time REAL DEFAULT 0.0"),
        ("categories", "ALTER TABLE blogs ADD COLUMN categories TEXT DEFAULT '[]'"),
    ]
    
    for col_name, sql in migrations:
        if col_name not in current_col_names:
            try:
                database.execute(sql)
                print(f"✓ Added column: {col_name}")
            except Exception as e:
                print(f"✗ Failed to add column {col_name}: {e}")
        else:
            print(f"- Column {col_name} already exists")
    
    # Verify new schema
    new_cols = database.fetch_all('PRAGMA table_info(blogs)')
    new_col_names = [col['name'] for col in new_cols]
    print(f"\nNew columns: {new_col_names}")
    
    # Generate slugs for existing blogs that don't have them
    print("\nGenerating slugs for existing blogs...")
    blogs = database.fetch_all("SELECT id, title, slug FROM blogs WHERE slug IS NULL OR slug = ''")
    for blog in blogs:
        slug = blog['title'].lower().replace(' ', '-').replace('&', 'and')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        database.execute(f"UPDATE blogs SET slug = '{slug}' WHERE id = {blog['id']}")
        print(f"✓ Generated slug for blog ID {blog['id']}: {slug}")
    
    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    migrate()
