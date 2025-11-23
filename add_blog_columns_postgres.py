"""
Add missing columns to blogs table in PostgreSQL database
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Parse PostgreSQL connection string
# postgresql://user:password@host/database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("Connected to PostgreSQL database")

# List of columns to add
columns_to_add = [
    ("slug", "VARCHAR(255) UNIQUE"),
    ("image_alt", "TEXT"),
    ("featured", "BOOLEAN DEFAULT FALSE"),
    ("meta_title", "TEXT"),
    ("meta_description", "TEXT"),
    ("canonical_url", "TEXT"),
    ("og_title", "TEXT"),
    ("og_description", "TEXT"),
    ("og_image_url", "TEXT"),
    ("og_image_alt", "TEXT"),
    ("word_count", "INTEGER DEFAULT 0"),
    ("reading_time", "FLOAT DEFAULT 0.0"),
    ("categories", "TEXT"),  # JSON stored as TEXT
]

print("\nAdding missing columns to blogs table...")

for column_name, column_type in columns_to_add:
    try:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='blogs' AND column_name=%s
        """, (column_name,))
        
        if cursor.fetchone() is None:
            # Column doesn't exist, add it
            sql = f"ALTER TABLE blogs ADD COLUMN {column_name} {column_type}"
            print(f"Adding column: {column_name}")
            cursor.execute(sql)
            conn.commit()
            print(f"  ✓ Added {column_name}")
        else:
            print(f"  - Column {column_name} already exists")
    except Exception as e:
        print(f"  ✗ Error adding {column_name}: {e}")
        conn.rollback()

print("\nGenerating slugs for existing blogs...")
try:
    # Generate slugs for blogs that don't have one
    cursor.execute("""
        UPDATE blogs 
        SET slug = LOWER(REGEXP_REPLACE(REGEXP_REPLACE(title, '[^a-zA-Z0-9\\s-]', '', 'g'), '\\s+', '-', 'g'))
        WHERE slug IS NULL OR slug = ''
    """)
    conn.commit()
    print(f"  ✓ Generated slugs for blogs")
except Exception as e:
    print(f"  ✗ Error generating slugs: {e}")
    conn.rollback()

cursor.close()
conn.close()

print("\n✓ Migration completed successfully!")
