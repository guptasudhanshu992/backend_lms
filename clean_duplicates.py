import sqlite3

def clean_duplicate_blogs():
    conn = sqlite3.connect("dev.db")
    cursor = conn.cursor()
    
    try:
        # Get all blogs
        cursor.execute("SELECT id, title, author FROM blogs ORDER BY id")
        all_blogs = cursor.fetchall()
        print(f"Total blogs before cleanup: {len(all_blogs)}")
        
        # Keep only the first 3 unique blogs (IDs 1, 2, 3)
        cursor.execute("DELETE FROM blogs WHERE id > 3")
        conn.commit()
        
        # Verify
        cursor.execute("SELECT id, title, author, category FROM blogs")
        remaining_blogs = cursor.fetchall()
        print(f"\nBlogs after cleanup: {len(remaining_blogs)}")
        for blog in remaining_blogs:
            print(f"  [{blog[0]}] {blog[1]} by {blog[2]} ({blog[3]})")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clean_duplicate_blogs()
