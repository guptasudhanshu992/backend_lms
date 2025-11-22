from fastapi import APIRouter, HTTPException
from app.services.stream_service import list_videos, store_video_reference

router = APIRouter()


@router.get("/stream/videos")
def get_stream_videos():
    try:
        videos = list_videos()
        # return simplified list
        return {"videos": [{"uid": v.get("uid"), "meta": v.get("meta", {})} for v in videos]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream/videos/store")
def store_video(video_id: str, note: str | None = None):
    try:
        store_video_reference(video_id, note or "")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Note: uploading video to Cloudflare Stream is typically done directly from client to Stream
# using a signed upload URL or via server-side with the Stream Upload API. This demo shows
# how to list videos and store references; to upload video bytes, call POST /accounts/:account_id/stream
# per Cloudflare Stream docs and provide `file` or `url`.
