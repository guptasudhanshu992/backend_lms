import sqlite3
import os

def apply_migration():
    db_path = "dev.db"
    migration_file = "app/migrations/003_create_content_tables.sql"
    
    if not os.path.exists(migration_file):
        print(f"Error: Migration file not found: {migration_file}")
        return
    
    # Read migration SQL
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Execute migration
        cursor.executescript(migration_sql)
        conn.commit()
        print("✓ Migration applied successfully!")
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM blogs")
        blog_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM courses")
        course_count = cursor.fetchone()[0]
        
        print(f"✓ Blogs in database: {blog_count}")
        print(f"✓ Courses in database: {course_count}")
        
        # Show blog titles
        cursor.execute("SELECT id, title, author, category FROM blogs WHERE published = 1")
        blogs = cursor.fetchall()
        print("\nPublished blogs:")
        for blog in blogs:
            print(f"  [{blog[0]}] {blog[1]} by {blog[2]} ({blog[3]})")
        
    except Exception as e:
        print(f"Error applying migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migration()
