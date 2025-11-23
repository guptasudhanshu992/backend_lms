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
from app.routers import profile as profile_router
try:
    from app.routers import admin as admin_router
except Exception:
    admin_router = None
try:
    from app.routers import admin_auth as admin_auth_router
except Exception:
    admin_auth_router = None
try:
    print(">>> Attempting to import content router...")
    from app.routers import content as content_router
    print(f">>> content_router loaded successfully!")
    print(f">>> Total routes in content_router: {len(content_router.router.routes)}")
    public_routes = [r.path for r in content_router.router.routes if 'public' in r.path]
    print(f">>> Public routes: {public_routes}")
except Exception as e:
    print(f">>> ERROR loading content_router: {e}")
    import traceback
    traceback.print_exc()
    content_router = None

try:
    from app.routers import payment as payment_router
except Exception as e:
    print(f">>> ERROR loading payment_router: {e}")
    payment_router = None

try:
    from app.routers import analytics as analytics_router
except Exception as e:
    print(f">>> ERROR loading analytics_router: {e}")
    analytics_router = None

try:
    from app.routers import quiz as quiz_router
except Exception as e:
    print(f">>> ERROR loading quiz_router: {e}")
    quiz_router = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lms.backend")

app = FastAPI(title="LMS Backend - FastAPI")

# Configure CORS - allow frontend origin or all origins in development
allowed_origins = []
if settings.FRONTEND_ORIGIN:
    # Support multiple origins separated by comma
    allowed_origins = [origin.strip() for origin in settings.FRONTEND_ORIGIN.split(',')]
else:
    # If not set, allow all (not recommended for production)
    allowed_origins = ["*"]

print(">>> FRONTEND_ORIGIN =", repr(settings.FRONTEND_ORIGIN))
print(">>> Allowed CORS origins:", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add analytics middleware to track all API requests
# DISABLED: Analytics middleware consumes significant resources
# try:
#     from app.middleware.analytics_middleware import APIAnalyticsMiddleware
#     app.add_middleware(APIAnalyticsMiddleware)
#     print(">>> API Analytics middleware enabled")
# except Exception as e:
#     print(f">>> WARNING: Could not enable analytics middleware: {e}")

print(">>> FRONTEND_ORIGIN =", repr(settings.FRONTEND_ORIGIN))

app.include_router(hello.router, prefix="/api")
app.include_router(r2.router, prefix="/api")
app.include_router(d1.router, prefix="/api")
app.include_router(stream.router, prefix="/api")

# Auth router
app.include_router(auth_router.router, prefix="/api/auth")

# Profile router
app.include_router(profile_router.router, prefix="/api/profile")

# Admin Auth router (env-based authentication)
if admin_auth_router is not None:
    app.include_router(admin_auth_router.router, prefix="/api/admin/auth")

# GDPR router
app.include_router(gdpr_router.router, prefix="/api/gdpr")

# Admin router (optional)
if admin_router is not None:
    app.include_router(admin_router.router, prefix="/api/admin")

# Content router (courses and blogs - includes both /admin and /public routes)
if content_router is not None:
    # Register with /api prefix - routes in content.py have /admin/... and /public/... prefixes
    app.include_router(content_router.router, prefix="/api")
    print(">>> Content router registered with /api/admin/* and /api/public/* routes")

# Payment router
if payment_router is not None:
    app.include_router(payment_router.router)
    print(">>> Payment router registered")

# Quiz router
if quiz_router is not None:
    app.include_router(quiz_router.router)
    print(">>> Quiz router registered")

# Analytics router
# DISABLED: Analytics feature consumes significant resources
# if analytics_router is not None:
#     app.include_router(analytics_router.router)
#     print(">>> Analytics router registered")

@app.on_event("startup")
async def startup_event():
    # run D1 migrations or initial checks
    logger.info("startup_event: starting init_db")
    t0 = time.time()

    '''
    try:
        d1_service.init_db()
    except Exception as e:
        logger.exception("startup_event: init_db failed: %s", e)
    finally:
        logger.info("startup_event: init_db completed in %.3f sec", time.time() - t0)
    '''
    
    # Bootstrap admin user from .env
    logger.info("startup_event: bootstrapping admin user")
    try:
        bootstrap_admin()
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
