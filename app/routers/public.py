from fastapi import APIRouter, HTTPException
from app.services.d1_service import database
from app.routers.content import blogs, courses
from sqlalchemy import text
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== Public Blog Endpoints =====

@router.get('/blogs')
def list_public_blogs(limit: int = 20, offset: int = 0):
    """List published blog posts (public endpoint) with pagination."""
    try:
        # Use raw SQL to safely handle missing columns
        query_text = """
            SELECT id, title, excerpt, content, author, category, image_url, published, created_at
            FROM blogs 
            WHERE published = TRUE 
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        result = database.fetch_all(query_text, {"limit": limit, "offset": offset})
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM blogs WHERE published = TRUE"
        total_result = database.fetch_one(count_query)
        total = total_result["total"] if total_result else 0
        
        logger.info(f"Fetched {len(result)} of {total} published blogs")
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
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error fetching blogs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching blogs: {str(e)}")


@router.get('/blogs/{blog_id}')
def get_public_blog(blog_id: int):
    """Get a specific published blog post (public endpoint)."""
    query = text("SELECT * FROM blogs WHERE id = :blog_id AND published = TRUE")
    blog = database.fetch_one(query, {"blog_id": blog_id})
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
def list_public_courses(limit: int = 20, offset: int = 0):
    """List published courses (public endpoint) with pagination."""
    print("Hello from list_public_courses")
    debug_log = open("debug_courses.txt", "a")
    debug_log.write(f"\n\n[DEBUG {__import__('datetime').datetime.now()}] list_public_courses called with limit={limit}, offset={offset}\n")
    try:
        debug_log.write("[DEBUG] Creating query for courses\n")
        query = text("SELECT * FROM courses WHERE published = TRUE ORDER BY created_at DESC LIMIT :limit OFFSET :offset")
        debug_log.write(f"[DEBUG] Query created: {query}\n")
        
        debug_log.write("[DEBUG] Executing fetch_all\n")
        result = database.fetch_all(query, {"limit": limit, "offset": offset})
        debug_log.write(f"[DEBUG] fetch_all completed, got {len(result)} results\n")
        
        # Get total count
        debug_log.write("[DEBUG] Creating count query\n")
        count_query = text("SELECT COUNT(*) as total FROM courses WHERE published = TRUE")
        debug_log.write("[DEBUG] Executing count query\n")
        total_result = database.fetch_one(count_query)
        debug_log.write(f"[DEBUG] Count query result: {total_result}\n")
        total = total_result["total"] if total_result else 0
        debug_log.write(f"[DEBUG] Total courses: {total}\n")
        
        logger.info(f"Fetched {len(result)} of {total} published courses")
        debug_log.write("[DEBUG] Building response data\n")
        courses_data = [
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
        debug_log.write(f"[DEBUG] Built {len(courses_data)} course objects\n")
        
        response = {
            "courses": courses_data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        debug_log.write(f"[DEBUG] Returning response with {len(courses_data)} courses\n")
        debug_log.close()
        return response
    except Exception as e:
        debug_log.write(f"[DEBUG ERROR] Exception caught: {type(e).__name__}: {str(e)}\n")
        logger.error(f"Error fetching courses: {str(e)}")
        import traceback
        debug_log.write(f"[DEBUG ERROR] Traceback: {traceback.format_exc()}\n")
        debug_log.close()
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")


@router.get('/courses/{course_id}')
def get_public_course(course_id: int):
    """Get a specific published course (public endpoint)."""
    query = text("SELECT * FROM courses WHERE id = :course_id AND published = TRUE")
    course = database.fetch_one(query, {"course_id": course_id})
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
