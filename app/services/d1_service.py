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
        migrations_path = os.path.join(os.path.dirname(__file__), "..", "migrations", "001_create_messages.sql")
        migrations_path = os.path.abspath(migrations_path)
        logger.info("d1.init_db: applying migration %s", migrations_path)
        with open(migrations_path, "r", encoding="utf-8") as f:
            migration_sql = f.read()
        t1 = time.time()
        # execute raw SQL
        await database.execute(query=migration_sql)
        logger.info("d1.init_db: migration applied (%.3f sec)", time.time() - t1)
    except Exception as e:
        # log and continue; often means table already exists
        logger.exception("d1.init_db: migration failed or skipped: %s", e)



async def create_message(content: str, video_id: str = None):
    query = "INSERT INTO messages (content, video_id) VALUES (:content, :video_id)"
    await database.execute(query=query, values={"content": content, "video_id": video_id})


async def list_messages(limit: int = 50):
    query = "SELECT id, content, created_at, video_id FROM messages ORDER BY id DESC LIMIT :limit"
    return await database.fetch_all(query=query, values={"limit": limit})
