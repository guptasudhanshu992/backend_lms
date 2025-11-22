from fastapi import APIRouter, HTTPException
from app.services.d1_service import database
from app.routers.content import blogs, courses
from sqlalchemy import text
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== Public Blog Endpoints =====

@router.get('/blogs')
async def list_public_blogs():
    """List all published blog posts (public endpoint)."""
    try:
        # Use raw SQL to safely handle missing columns
        query_text = """
            SELECT id, title, excerpt, content, author, category, image_url, published, created_at
            FROM blogs 
            WHERE published = TRUE 
            ORDER BY created_at DESC
        """
        result = await database.fetch_all(query_text)
        logger.info(f"Fetched {len(result)} published blogs")
        return {
            "blogs": [
                {
                    "id": b["id"],
                    "title": b["title"],
                    "excerpt": b["excerpt"],
                    "content": b["content"],
                    "author": b["author"],
                    "category": b["category"],
                    "image_url": b["image_url"],
                    "published": bool(b["published"]),
                    "created_at": b["created_at"] if isinstance(b["created_at"], str) else (b["created_at"].isoformat() if b.get("created_at") else None),
                }
                for b in result
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching blogs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching blogs: {str(e)}")


@router.get('/blogs/{blog_id}')
async def get_public_blog(blog_id: int):
    """Get a specific published blog post (public endpoint)."""
    query = text("SELECT * FROM blogs WHERE id = :blog_id AND published = TRUE")
    blog = await database.fetch_one(query, {"blog_id": blog_id})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return {
        "id": blog["id"],
        "title": blog["title"],
        "excerpt": blog["excerpt"],
        "content": blog["content"],
        "author": blog["author"],
        "category": blog["category"],
        "image_url": blog["image_url"],
        "published": blog["published"],
        "created_at": blog["created_at"].isoformat() if hasattr(blog["created_at"], 'isoformat') else str(blog["created_at"]),
    }


# ===== Public Courses Endpoints =====

@router.get('/courses')
async def list_public_courses():
    """List all published courses (public endpoint)."""
    try:
        query = text("SELECT * FROM courses WHERE published = TRUE ORDER BY created_at DESC")
        result = await database.fetch_all(query)
        return {
            "courses": [
                {
                    "id": c["id"],
                    "title": c["title"],
                    "description": c["description"],
                    "instructor": c["instructor"],
                    "duration": c["duration"],
                    "level": c["level"],
                    "category": c["category"],
                    "image_url": c.get("image_url"),
                    "published": c["published"],
                    "created_at": c["created_at"].isoformat() if hasattr(c.get("created_at"), 'isoformat') else str(c.get("created_at")) if c.get("created_at") else None,
                }
                for c in result
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")


@router.get('/courses/{course_id}')
async def get_public_course(course_id: int):
    """Get a specific published course (public endpoint)."""
    query = text("SELECT * FROM courses WHERE id = :course_id AND published = TRUE")
    course = await database.fetch_one(query, {"course_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {
        "id": course["id"],
        "title": course["title"],
        "description": course["description"],
        "instructor": course["instructor"],
        "duration": course["duration"],
        "level": course["level"],
        "category": course["category"],
        "image_url": course.get("image_url"),
        "published": course["published"],
        "created_at": course["created_at"].isoformat() if hasattr(course.get("created_at"), 'isoformat') else str(course.get("created_at")) if course.get("created_at") else None,
    }
