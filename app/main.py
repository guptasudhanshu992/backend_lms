from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

# Import routers after settings (and after loading .env) so settings pick up env values
from app.api import hello, r2, d1, stream
from app.services import d1_service

app = FastAPI(title="LMS Backend - FastAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello.router, prefix="/api")
app.include_router(r2.router, prefix="/api")
app.include_router(d1.router, prefix="/api")
app.include_router(stream.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    # run D1 migrations or initial checks
    await d1_service.init_db()
