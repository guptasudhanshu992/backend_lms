from dotenv import load_dotenv
load_dotenv()

import logging
import time
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

# Import routers after settings (and after loading .env) so settings pick up env values
from app.api import hello, r2, d1, stream
from app.services import d1_service
from app.services.admin_bootstrap import bootstrap_admin
from app.routers import auth as auth_router
from app.routers import gdpr as gdpr_router
try:
    from app.routers import admin as admin_router
except Exception:
    admin_router = None
try:
    from app.routers import admin_auth as admin_auth_router
except Exception:
    admin_auth_router = None
try:
    from app.routers import content as content_router
except Exception:
    content_router = None
try:
    from app.routers import public as public_router
except Exception:
    public_router = None

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

print(">>> FRONTEND_ORIGIN =", repr(settings.FRONTEND_ORIGIN))

app.include_router(hello.router, prefix="/api")
app.include_router(r2.router, prefix="/api")
app.include_router(d1.router, prefix="/api")
app.include_router(stream.router, prefix="/api")

# Auth router
app.include_router(auth_router.router, prefix="/api/auth")

# Admin Auth router (env-based authentication)
if admin_auth_router is not None:
    app.include_router(admin_auth_router.router, prefix="/api/admin/auth")

# GDPR router
app.include_router(gdpr_router.router, prefix="/api/gdpr")

# Public router (blogs, courses)
if public_router is not None:
    app.include_router(public_router.router, prefix="/api/public")

# Admin router (optional)
if admin_router is not None:
    app.include_router(admin_router.router, prefix="/api/admin")

# Content router (courses and blogs)
if content_router is not None:
    app.include_router(content_router.router, prefix="/api/admin")

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
    
    # Bootstrap admin user from .env
    logger.info("startup_event: bootstrapping admin user")
    try:
        await bootstrap_admin()
    except Exception as e:
        logger.exception("startup_event: bootstrap_admin failed: %s", e)
    
    # Start background scheduler for auto-publishing blogs
    logger.info("startup_event: starting blog scheduler")
    # Temporarily disabled for debugging
    # try:
    #     from app.tasks.scheduler import check_and_publish_scheduled_blogs
    #     asyncio.create_task(run_blog_scheduler(check_and_publish_scheduled_blogs))
    # except Exception as e:
    #     logger.exception("startup_event: blog scheduler failed to start: %s", e)


async def run_blog_scheduler(check_func):
    """Run the blog scheduler in the background"""
    while True:
        try:
            await check_func()
        except Exception as e:
            logger.error(f"Blog scheduler error: {e}")
        await asyncio.sleep(60)  # Check every minute
