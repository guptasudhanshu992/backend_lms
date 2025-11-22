from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.d1_service import create_message, list_messages, database

router = APIRouter()


class MessageIn(BaseModel):
    content: str
    video_id: str | None = None


@router.on_event("startup")
async def _connect_db():
    if not database._connected:
        await database.connect()


@router.post("/d1/messages")
async def post_message(msg: MessageIn):
    try:
        await create_message(msg.content, msg.video_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/d1/messages")
async def get_messages():
    try:
        msgs = await list_messages()
        return {"messages": [dict(m) for m in msgs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
