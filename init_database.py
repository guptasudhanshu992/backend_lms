"""
Database initialization script for LMS
Creates all tables in one go - works with both SQLite and PostgreSQL
Run this script to initialize a fresh database
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables BEFORE importing settings
from dotenv import load_dotenv
load_dotenv()

from app.config.settings import settings
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

# SQL statements to create all tables
CREATE_TABLES_SQL = """
-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT,
    full_name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role TEXT DEFAULT 'student',
    consent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    user_agent TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Email verification tokens
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Password reset tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- OAuth accounts
CREATE TABLE IF NOT EXISTS oauth_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    provider_user_id TEXT NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(provider, provider_user_id)
);

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    permissions TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Groups table
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    permissions TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User groups mapping
CREATE TABLE IF NOT EXISTS user_groups (
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    instructor TEXT,
    duration TEXT,
    level TEXT,
    category TEXT,
    image_url TEXT,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blogs table
CREATE TABLE IF NOT EXISTS blogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,
    author TEXT,
    category TEXT,
    image_url TEXT,
    published BOOLEAN DEFAULT FALSE,
    publish_at TIMESTAMP,
    tags TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blog tags junction table
CREATE TABLE IF NOT EXISTS blog_tags (
    blog_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (blog_id, tag_id),
    FOREIGN KEY (blog_id) REFERENCES blogs(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Insert default categories
INSERT OR IGNORE INTO categories (name, slug, description) VALUES
    ('Market Analysis', 'market-analysis', 'In-depth analysis of market trends'),
    ('Investment Tips', 'investment-tips', 'Practical investment advice'),
    ('Trading Strategies', 'trading-strategies', 'Expert trading strategies'),
    ('Financial News', 'financial-news', 'Latest financial updates'),
    ('Industry Insights', 'industry-insights', 'Industry trends and insights');
"""

# PostgreSQL-specific SQL (uses SERIAL instead of AUTOINCREMENT)
CREATE_TABLES_POSTGRESQL = """
-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT,
    full_name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role TEXT DEFAULT 'student',
    consent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    user_agent TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Email verification tokens
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Password reset tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- OAuth accounts
CREATE TABLE IF NOT EXISTS oauth_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    provider_user_id TEXT NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(provider, provider_user_id)
);

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    permissions TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Groups table
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    permissions TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User groups mapping
CREATE TABLE IF NOT EXISTS user_groups (
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    instructor TEXT,
    duration TEXT,
    level TEXT,
    category TEXT,
    image_url TEXT,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blogs table
CREATE TABLE IF NOT EXISTS blogs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,
    author TEXT,
    category TEXT,
    image_url TEXT,
    published BOOLEAN DEFAULT FALSE,
    publish_at TIMESTAMP,
    tags TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blog tags junction table
CREATE TABLE IF NOT EXISTS blog_tags (
    blog_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (blog_id, tag_id),
    FOREIGN KEY (blog_id) REFERENCES blogs(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Insert default categories (ON CONFLICT DO NOTHING for PostgreSQL)
INSERT INTO categories (name, slug, description) VALUES
    ('Market Analysis', 'market-analysis', 'In-depth analysis of market trends'),
    ('Investment Tips', 'investment-tips', 'Practical investment advice'),
    ('Trading Strategies', 'trading-strategies', 'Expert trading strategies'),
    ('Financial News', 'financial-news', 'Latest financial updates'),
    ('Industry Insights', 'industry-insights', 'Industry trends and insights')
ON CONFLICT (name) DO NOTHING;
"""


def init_database():
    """Initialize database with all tables"""
    print(f"🔗 Connecting to database: {settings.DATABASE_URL}")
    
    # Determine if we're using PostgreSQL
    is_postgres = settings.DATABASE_URL.startswith('postgresql')
    
    # Create engine with appropriate configuration
    if is_postgres:
        engine = create_engine(settings.DATABASE_URL)
    else:
        # SQLite needs special handling for file paths
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
    
    try:
        connection = engine.connect()
        print("✅ Connected to database")
        
        # Choose appropriate SQL based on database type
        sql = CREATE_TABLES_POSTGRESQL if is_postgres else CREATE_TABLES_SQL
        print(f"  📝 Using {'PostgreSQL' if is_postgres else 'SQLite'} SQL syntax")
        
        # Get existing tables before execution
        print("  🔍 Checking existing tables...")
        if is_postgres:
            pre_verify_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
        else:
            pre_verify_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%%'"
        
        try:
            result = connection.execute(text(pre_verify_query))
            existing_before = set(row[0] for row in result)
            print(f"  📊 Found {len(existing_before)} existing tables: {', '.join(sorted(existing_before)) if existing_before else 'none'}")
        except Exception:
            existing_before = set()
        
        # Split and execute statements - filter out comments and empty lines
        raw_statements = sql.split(';')
        statements = []
        for stmt in raw_statements:
            # Remove comments and whitespace
            lines = [line for line in stmt.split('\n') if line.strip() and not line.strip().startswith('--')]
            clean_stmt = '\n'.join(lines).strip()
            if clean_stmt and len(clean_stmt) > 20:  # Only keep substantial statements
                statements.append(clean_stmt)
        
        print(f"📋 Found {len(statements)} SQL statements to execute...")
        
        created_tables = []
        failed_statements = []
        
        for i, stmt in enumerate(statements, 1):
            try:
                print(f"  🔄 Executing statement {i}/{len(statements)}...")
                
                # Show a preview of the statement
                stmt_preview = stmt[:100].replace('\n', ' ').strip()
                if len(stmt) > 100:
                    stmt_preview += "..."
                print(f"     Query: {stmt_preview}")
                
                connection.execute(text(stmt))
                connection.commit()
                
                # Show progress for important operations
                if 'CREATE TABLE' in stmt:
                    table_name = stmt.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
                    print(f"  ✅ Created/verified table: {table_name}")
                    created_tables.append(table_name)
                elif 'INSERT' in stmt and 'categories' in stmt:
                    print(f"  ✅ Inserted default categories")
                else:
                    print(f"  ✅ Statement {i} executed successfully")
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ Statement {i} failed!")
                print(f"     Error type: {type(e).__name__}")
                print(f"     Error message: {error_msg}")
                print(f"     Failed query preview: {stmt[:300]}...")
                # Print full traceback for debugging
                import traceback
                print(f"     Full error details:")
                traceback.print_exc()
                failed_statements.append({
                    'statement_num': i,
                    'error_type': type(e).__name__,
                    'error_message': error_msg,
                    'query_preview': stmt[:200]
                })
                continue
        
        # Verify tables exist
        print("\n🔍 Verifying created tables...")
        if is_postgres:
            verify_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """
        else:
            verify_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%%' ORDER BY name"
        
        existing_tables = []
        new_tables = []
        existing_tables_count = 0
        
        try:
            result = connection.execute(text(verify_query))
            existing_tables = [row[0] for row in result]
            
            # Calculate what's new vs what existed
            existing_after = set(existing_tables)
            new_tables = list(existing_after - existing_before)
            existed_before = list(existing_after & existing_before)
            
            print(f"✅ Found {len(existing_tables)} tables in database:")
            for table in existing_tables:
                status = "🆕 NEW" if table in new_tables else "✓"
                print(f"   {status} {table}")
        except Exception as e:
            print(f"⚠️  Could not verify tables: {e}")
            new_tables = []
            existed_before = []
        
        print("\n" + "=" * 60)
        print(f"✅ Database initialization complete!")
        print(f"📊 Database type: {'PostgreSQL' if is_postgres else 'SQLite'}")
        print(f"📋 Total tables: {len(existing_tables)}")
        print(f"🆕 Newly created: {len(new_tables)}")
        print(f"✓  Already existed: {len(existed_before)}")
        
        if failed_statements:
            print(f"\n⚠️  WARNING: {len(failed_statements)} statement(s) failed:")
            print("=" * 60)
            for fail in failed_statements:
                print(f"\n❌ Statement #{fail['statement_num']}:")
                print(f"   Error Type: {fail['error_type']}")
                print(f"   Error: {fail['error_message']}")
                print(f"   Query: {fail['query_preview']}")
                if len(fail['query_preview']) == 200:
                    print(f"   (truncated...)")
            print("=" * 60)
        else:
            print("✅ All statements executed successfully!")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during database initialization!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("\n📋 Full Traceback:")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("=" * 60)
        raise
    finally:
        connection.close()
        engine.dispose()
        print("🔌 Disconnected from database")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 LMS Database Initialization Script")
    print("=" * 60)
    print()
    
    init_database()
    
    print()
    print("=" * 60)
    print("✨ You can now start your application!")
    print("=" * 60)
