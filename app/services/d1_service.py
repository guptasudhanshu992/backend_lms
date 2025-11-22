import logging
import time
import sqlalchemy
from sqlalchemy import text, create_engine
from sqlalchemy.pool import StaticPool, QueuePool
from app.config.settings import settings
import os

logger = logging.getLogger("lms.d1")

DATABASE_URL = settings.DATABASE_URL

# Create engine based on database type
is_postgres = DATABASE_URL.startswith('postgresql')
if is_postgres:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )


def get_connection():
    """Get a fresh database connection from the pool"""
    return engine.connect()


# Create a database-like object for backward compatibility
class DatabaseWrapper:
    """Wrapper to provide databases-library-like interface"""
    
    def __init__(self):
        self._connected = False
    
    def connect(self):
        """Connect to database (no-op as connection is managed by pool)"""
        self._connected = True
    
    def disconnect(self):
        """Disconnect from database (connections returned to pool automatically)"""
        self._connected = False
    
    def execute(self, query, values=None):
        """Execute a query and return result"""
        connection = get_connection()
        try:
            # Handle both text queries and SQLAlchemy selectables
            if isinstance(query, str):
                query = text(query)
            
            result = connection.execute(query, values or {})
            connection.commit()
            
            # Return last inserted ID if available
            if hasattr(result, 'lastrowid'):
                return result.lastrowid
            return result
        except Exception as e:
            connection.rollback()
            logger.error(f"Database execute error: {e}")
            raise
        finally:
            connection.close()
    
    def fetch_all(self, query, values=None):
        """Fetch all rows from a query"""
        connection = get_connection()
        try:
            # Handle both text queries and SQLAlchemy selectables
            if isinstance(query, str):
                query = text(query)
            
            result = connection.execute(query, values or {})
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            connection.rollback()
            logger.error(f"Database fetch_all error: {e}")
            raise
        finally:
            connection.close()
    
    def fetch_one(self, query, values=None):
        """Fetch one row from a query"""
        connection = get_connection()
        try:
            # Handle both text queries and SQLAlchemy selectables
            if isinstance(query, str):
                query = text(query)
            
            result = connection.execute(query, values or {})
            row = result.fetchone()
            return dict(row._mapping) if row else None
        except Exception as e:
            connection.rollback()
            logger.error(f"Database fetch_one error: {e}")
            raise
        finally:
            connection.close()
    
    def fetch_val(self, query, values=None):
        """Fetch a single value from a query"""
        connection = get_connection()
        try:
            # Handle both text queries and SQLAlchemy selectables
            if isinstance(query, str):
                query = text(query)
            
            result = connection.execute(query, values or {})
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            connection.rollback()
            logger.error(f"Database fetch_val error: {e}")
            raise
        finally:
            connection.close()

# Export database instance for backward compatibility
database = DatabaseWrapper()


def init_db():
    # connect and run SQL migrations (demo: run single SQL file)
    t0 = time.time()
    logger.info("d1.init_db: connecting to database at %s", DATABASE_URL)
    connection = get_connection()
    logger.info("d1.init_db: connected (%.3f sec)", time.time() - t0)
    try:
        # apply existing migrations
        migrations_dir = os.path.join(os.path.dirname(__file__), "..", "migrations")
        migrations_dir = os.path.abspath(migrations_dir)
        for fname in sorted(os.listdir(migrations_dir)):
            if fname.endswith('.sql'):
                path = os.path.join(migrations_dir, fname)
                logger.info("d1.init_db: applying migration %s", path)
                with open(path, "r", encoding="utf-8") as f:
                    migration_sql = f.read()
                
                # Split SQL statements (SQLite can only execute one at a time)
                # Remove comments and split by semicolon
                lines = []
                for line in migration_sql.split('\n'):
                    # Remove comments
                    line = line.split('--')[0].strip()
                    if line:
                        lines.append(line)
                
                full_sql = ' '.join(lines)
                statements = [
                    stmt.strip() 
                    for stmt in full_sql.split(';') 
                    if stmt.strip()
                ]
                
                t1 = time.time()
                for i, stmt in enumerate(statements):
                    try:
                        logger.debug("Executing statement %d: %s...", i+1, stmt[:100])
                        connection.execute(text(stmt))
                        connection.commit()
                    except Exception as e:
                        # Table might already exist, rollback and continue
                        connection.rollback()
                        logger.warning("Statement %d failed (may be expected): %s", i+1, str(e))
                
                logger.info("d1.init_db: applied %s (%d statements) in %.3f sec", fname, len(statements), time.time() - t1)
    except Exception as e:
        connection.rollback()
        logger.exception("d1.init_db: migration failed or skipped: %s", e)
    finally:
        connection.close()



def create_message(content: str, video_id: str = None):
    connection = get_connection()
    try:
        query = text("INSERT INTO messages (content, video_id) VALUES (:content, :video_id)")
        connection.execute(query, {"content": content, "video_id": video_id})
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_messages(limit: int = 50):
    connection = get_connection()
    try:
        query = text("SELECT id, content, created_at, video_id FROM messages ORDER BY id DESC LIMIT :limit")
        result = connection.execute(query, {"limit": limit})
        # Convert result to list of dicts to match the original interface
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        connection.rollback()
        raise
    finally:
        connection.close()
