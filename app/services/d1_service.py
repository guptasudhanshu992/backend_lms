import sqlalchemy
from sqlalchemy import text
from app.config.settings import settings
import databases
import os

DATABASE_URL = settings.DATABASE_URL
database = databases.Database(DATABASE_URL)


async def init_db():
    # connect and run SQL migrations (demo: run single SQL file)
    await database.connect()
    try:
        migrations_path = os.path.join(os.path.dirname(__file__), "..", "migrations", "001_create_messages.sql")
        migrations_path = os.path.abspath(migrations_path)
        with open(migrations_path, "r", encoding="utf-8") as f:
            migration_sql = f.read()
        # execute raw SQL
        await database.execute(query=migration_sql)
    except Exception:
        # ignore if already created
        pass


async def create_message(content: str, video_id: str = None):
    query = "INSERT INTO messages (content, video_id) VALUES (:content, :video_id)"
    await database.execute(query=query, values={"content": content, "video_id": video_id})


async def list_messages(limit: int = 50):
    query = "SELECT id, content, created_at, video_id FROM messages ORDER BY id DESC LIMIT :limit"
    return await database.fetch_all(query=query, values={"limit": limit})
