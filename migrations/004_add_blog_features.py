"""
Migration to add:
1. Tags table
2. Categories table  
3. Blog tags many-to-many relationship
4. publish_at datetime field to blogs
"""
import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.d1_service import database

async def upgrade():
    """Apply migration."""
    
    # Create categories table
    await database.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create tags table
    await database.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create blog_tags junction table
    await database.execute("""
        CREATE TABLE IF NOT EXISTS blog_tags (
            blog_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (blog_id, tag_id),
            FOREIGN KEY (blog_id) REFERENCES blogs (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        )
    """)
    
    # Add publish_at column to blogs table (check if it exists first)
    try:
        await database.execute("""
            ALTER TABLE blogs ADD COLUMN publish_at TIMESTAMP NULL
        """)
    except Exception as e:
        if "duplicate column" not in str(e).lower():
            raise
        print("publish_at column already exists, skipping")
    
    # Add tags column to blogs table (JSON string for tag IDs)
    try:
        await database.execute("""
            ALTER TABLE blogs ADD COLUMN tags TEXT DEFAULT '[]'
        """)
    except Exception as e:
        if "duplicate column" not in str(e).lower():
            raise
        print("tags column already exists, skipping")
    
    # Insert default categories
    default_categories = [
        ('Market Analysis', 'market-analysis', 'Analysis of market trends and movements'),
        ('Investment Tips', 'investment-tips', 'Tips and strategies for investments'),
        ('Trading Strategies', 'trading-strategies', 'Various trading strategies and techniques'),
        ('Financial News', 'financial-news', 'Latest news in finance and economics'),
        ('Industry Insights', 'industry-insights', 'Insights into various industries'),
    ]
    
    for name, slug, desc in default_categories:
        await database.execute(
            "INSERT OR IGNORE INTO categories (name, slug, description) VALUES (:name, :slug, :description)",
            {"name": name, "slug": slug, "description": desc}
        )
    
    print("Migration 004 completed: Added tags, categories, and publish_at fields")

async def downgrade():
    """Revert migration."""
    await database.execute("DROP TABLE IF EXISTS blog_tags")
    await database.execute("DROP TABLE IF EXISTS tags")
    await database.execute("DROP TABLE IF EXISTS categories")
    # Note: SQLite doesn't support DROP COLUMN, so we can't easily remove the columns
    print("Migration 004 reverted")

if __name__ == "__main__":
    asyncio.run(upgrade())
