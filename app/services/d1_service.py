import logging
import time
import sqlalchemy
from sqlalchemy import text
from app.config.settings import settings
import databases
import os

logger = logging.getLogger("lms.d1")

DATABASE_URL = settings.DATABASE_URL
database = databases.Database(DATABASE_URL)


async def init_db():
    # connect and run SQL migrations (demo: run single SQL file)
    t0 = time.time()
    logger.info("d1.init_db: connecting to database at %s", DATABASE_URL)
    await database.connect()
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
                        await database.execute(query=stmt)
                    except Exception as e:
                        # Table might already exist, log but continue
                        logger.warning("Statement %d failed (may be expected): %s", i+1, str(e))
                
                logger.info("d1.init_db: applied %s (%d statements) in %.3f sec", fname, len(statements), time.time() - t1)
    except Exception as e:
        logger.exception("d1.init_db: migration failed or skipped: %s", e)



async def create_message(content: str, video_id: str = None):
    query = "INSERT INTO messages (content, video_id) VALUES (:content, :video_id)"
    await database.execute(query=query, values={"content": content, "video_id": video_id})


async def list_messages(limit: int = 50):
    query = "SELECT id, content, created_at, video_id FROM messages ORDER BY id DESC LIMIT :limit"
    return await database.fetch_all(query=query, values={"limit": limit})
