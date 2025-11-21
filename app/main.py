from dotenv import load_dotenv
load_dotenv()

import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

# Import routers after settings (and after loading .env) so settings pick up env values
from app.api import hello, r2, d1, stream
from app.services import d1_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lms.backend")

app = FastAPI(title="LMS Backend - FastAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello.router, prefix="/api")
# Also register the hello router at the root so `/hello` works as an alias for quick testing
app.include_router(hello.router, prefix="")
app.include_router(r2.router, prefix="/api")
app.include_router(d1.router, prefix="/api")
app.include_router(stream.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    # run D1 migrations or initial checks
    logger.info("startup_event: starting init_db")
    t0 = time.time()
    try:
        await d1_service.init_db()
    except Exception as e:
        logger.exception("startup_event: init_db failed: %s", e)
    finally:
        logger.info("startup_event: init_db completed in %.3f sec", time.time() - t0)
