from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.d1_service import database
from app import models

router = APIRouter()


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_verified: bool
    role: str


@router.get('/me')
async def me():
    # placeholder: in real app, decode JWT and return user
    return {"ok": True, "user": None}


@router.get('/')
async def list_users():
    rows = await database.fetch_all(models.users.select())
    return {"users": [dict(r) for r in rows]}
