import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.d1_service import database
from app.routers.content import blogs

async def check_blogs():
    await database.connect()
    result = await database.fetch_all(blogs.select())
    print(f'Total blogs: {len(result)}')
    for b in result:
        print(f'ID: {b["id"]}, Published: {b.get("published")}, Title: {b["title"]}, Publish_at: {b.get("publish_at")}')
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(check_blogs())
