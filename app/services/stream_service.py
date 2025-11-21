import httpx
from app.config.settings import settings
from app.services.d1_service import create_message


CF_ACCOUNT_ID = settings.CF_ACCOUNT_ID
CF_STREAM_TOKEN = settings.CF_STREAM_TOKEN


async def list_videos():
    if not CF_ACCOUNT_ID or not CF_STREAM_TOKEN:
        return []
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/stream"
    headers = {"Authorization": f"Bearer {CF_STREAM_TOKEN}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, params={"per_page": 50})
        r.raise_for_status()
        data = r.json()
        # data['result'] is a list of videos
        return data.get("result", [])


async def store_video_reference(video_id: str, note: str = ""):
    # Example: store video id in D1 messages table for demo
    await create_message(content=f"Video {video_id}: {note}", video_id=video_id)
