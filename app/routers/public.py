from fastapi import APIRouter, HTTPException
from app.services.d1_service import database
from app.routers.content import blogs, courses
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
            WHERE published = 1 
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
    query = blogs.select().where(blogs.c.id == blog_id, blogs.c.published == True)
    blog = await database.fetch_one(query)
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
        "created_at": blog["created_at"].isoformat() if blog["created_at"] else None,
    }


# ===== Public Courses Endpoints =====

@router.get('/courses')
async def list_public_courses():
    """List all published courses (public endpoint)."""
    query = courses.select().where(courses.c.published == True).order_by(courses.c.created_at.desc())
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
                "price": c["price"],
                "category": c["category"],
                "image_url": c["image_url"],
                "published": c["published"],
                "created_at": c["created_at"].isoformat() if c["created_at"] else None,
            }
            for c in result
        ]
    }


@router.get('/courses/{course_id}')
async def get_public_course(course_id: int):
    """Get a specific published course (public endpoint)."""
    query = courses.select().where(courses.c.id == course_id, courses.c.published == True)
    course = await database.fetch_one(query)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {
        "id": course["id"],
        "title": course["title"],
        "description": course["description"],
        "instructor": course["instructor"],
        "duration": course["duration"],
        "level": course["level"],
        "price": course["price"],
        "category": course["category"],
        "image_url": course["image_url"],
        "published": course["published"],
        "created_at": course["created_at"].isoformat() if course["created_at"] else None,
    }
