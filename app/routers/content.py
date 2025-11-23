from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.dependencies import require_admin
from app.services.d1_service import database
from app.models import metadata
from sqlalchemy import Table, Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.sql import func
import json

logger = logging.getLogger(__name__)

router = APIRouter()

# Define blogs table
blogs = Table(
    "blogs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("slug", String, nullable=False, unique=True),
    Column("excerpt", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("author", String, nullable=False),
    Column("categories", Text, default='[]'),
    Column("tags", Text, default='[]'),
    Column("image_url", String, nullable=True),
    Column("image_alt", String, nullable=True),
    Column("featured", Boolean, default=False),
    Column("meta_title", String, nullable=True),
    Column("meta_description", String, nullable=True),
    Column("canonical_url", String, nullable=True),
    Column("og_title", String, nullable=True),
    Column("og_description", String, nullable=True),
    Column("og_image_url", String, nullable=True),
    Column("og_image_alt", String, nullable=True),
    Column("word_count", Integer, default=0),
    Column("reading_time", Float, default=0.0),
    Column("published", Boolean, default=False),
    Column("publish_at", DateTime, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
)

# Define courses table
courses = Table(
    "courses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("description", Text, nullable=False),
    Column("instructor", String, nullable=False),
    Column("duration", String, nullable=False),
    Column("level", String, nullable=False),
    Column("price", Float, nullable=False),
    Column("category", String, nullable=False),
    Column("image_url", String, nullable=True),
    Column("published", Boolean, default=True),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
)

@router.get('/admin/courses', dependencies=[Depends(require_admin)])
def list_courses(skip: int = 0, limit: int = 100):
    """List all courses."""
    query = courses.select().offset(skip).limit(limit).order_by(courses.c.created_at.desc())
    result = database.fetch_all(query)
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

# Define categories table
categories = Table(
    "categories",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("slug", String, nullable=False, unique=True),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)

# Define tags table
tags_table = Table(
    "tags",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("slug", String, nullable=False, unique=True),
    Column("created_at", DateTime, server_default=func.now()),
)

# Define blog_tags junction table
blog_tags = Table(
    "blog_tags",
    metadata,
    Column("blog_id", Integer, nullable=False),
    Column("tag_id", Integer, nullable=False),
)


# ===== Request/Response Models =====

class CourseCreate(BaseModel):
    title: str
    description: str
    instructor: str
    duration: str
    level: str
    price: float
    category: str
    image_url: Optional[str] = None
    published: bool = True


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructor: Optional[str] = None
    duration: Optional[str] = None
    level: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    published: Optional[bool] = None


class BlogCreate(BaseModel):
    title: str
    slug: str
    excerpt: str
    content: str
    author: str
    categories: Optional[List[int]] = []
    tags: Optional[List[int]] = []
    image_url: Optional[str] = None
    image_alt: Optional[str] = None
    featured: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image_url: Optional[str] = None
    og_image_alt: Optional[str] = None
    published: bool = False
    publish_at: Optional[datetime] = None


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TagCreate(BaseModel):
    name: str


class TagUpdate(BaseModel):
    name: Optional[str] = None


class BlogUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    categories: Optional[List[int]] = None
    tags: Optional[List[int]] = None
    image_url: Optional[str] = None
    image_alt: Optional[str] = None
    featured: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image_url: Optional[str] = None


@router.post('/admin/courses', dependencies=[Depends(require_admin)])
def create_course(payload: CourseCreate):
    """Create a new course."""
    query = courses.insert().values(
        title=payload.title,
        description=payload.description,
        instructor=payload.instructor,
        duration=payload.duration,
        level=payload.level,
        price=payload.price,
        category=payload.category,
        image_url=payload.image_url,
        published=payload.published,
    )
    course_id = database.execute(query)
    return {"id": course_id, "message": "Course created successfully"}


@router.get('/admin/courses/{course_id}', dependencies=[Depends(require_admin)])
def get_course(course_id: int):
    """Get a specific course."""
    query = courses.select().where(courses.c.id == course_id)
    course = database.fetch_one(query)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return dict(course)


@router.put('/admin/courses/{course_id}', dependencies=[Depends(require_admin)])
def update_course(course_id: int, payload: CourseUpdate):
    """Update a course."""
    # Check if course exists
    check_query = courses.select().where(courses.c.id == course_id)
    existing = database.fetch_one(check_query)
    if not existing:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Build update values
    update_values = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if not update_values:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    query = courses.update().where(courses.c.id == course_id).values(**update_values)
    database.execute(query)
    return {"message": "Course updated successfully"}


@router.delete('/admin/courses/{course_id}', dependencies=[Depends(require_admin)])
def delete_course(course_id: int):
    """Delete a course."""
    query = courses.delete().where(courses.c.id == course_id)
    database.execute(query)
    return {"message": "Course deleted successfully"}


# ===== Blog Management =====

@router.get('/admin/blogs', dependencies=[Depends(require_admin)])
def list_blogs(
    skip: int = 0,
    limit: int = 100,
):
    """List all blog posts."""
    try:
        query = blogs.select().offset(skip).limit(limit).order_by(blogs.c.created_at.desc())
        result = database.fetch_all(query)
        
        blogs_list = []
        for b in result:
            # Safely parse JSON fields
            try:
                categories = json.loads(b.get("categories")) if b.get("categories") and b.get("categories") != "" else []
            except (json.JSONDecodeError, TypeError):
                categories = []
            
            try:
                tags = json.loads(b.get("tags")) if b.get("tags") and b.get("tags") != "" else []
            except (json.JSONDecodeError, TypeError):
                tags = []
            
            blog_dict = {
                "id": b["id"],
                "title": b["title"],
                "slug": b.get("slug", ""),
                "excerpt": b.get("excerpt", ""),
                "content": b.get("content", ""),
                "author": b.get("author", ""),
                "category": b.get("category", ""),
                "categories": categories,
                "tags": tags,
                "image_url": b.get("image_url"),
                "image_alt": b.get("image_alt"),
                "featured": b.get("featured", False),
                "meta_title": b.get("meta_title"),
                "meta_description": b.get("meta_description"),
                "canonical_url": b.get("canonical_url"),
                "og_title": b.get("og_title"),
                "og_description": b.get("og_description"),
                "og_image_url": b.get("og_image_url"),
                "og_image_alt": b.get("og_image_alt"),
                "word_count": b.get("word_count", 0),
                "reading_time": b.get("reading_time", 0.0),
                "published": b.get("published", False),
                "publish_at": b["publish_at"].isoformat() if b.get("publish_at") else None,
                "created_at": b["created_at"].isoformat() if b.get("created_at") else None,
                "updated_at": b["updated_at"].isoformat() if b.get("updated_at") else None,
            }
            
            blogs_list.append(blog_dict)
        
        return {"blogs": blogs_list}
    except Exception as e:
        logger.error(f"Error listing blogs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching blogs: {str(e)}")


@router.post('/admin/blogs', dependencies=[Depends(require_admin)])
def create_blog(payload: BlogCreate):
    """Create a new blog post."""
    try:
        # Validate publish_at is in the future if provided
        if payload.publish_at and payload.publish_at <= datetime.utcnow():
            raise HTTPException(status_code=400, detail="Publish date must be in the future")

        # Slug uniqueness check
        existing_slug = database.fetch_one(blogs.select().where(blogs.c.slug == payload.slug))
        if existing_slug:
            raise HTTPException(status_code=400, detail="Slug already exists. Please choose a unique slug.")

        # Word count and reading time
        import re
        text_content = re.sub('<[^<]+?>', '', payload.content or '')
        word_count = len(text_content.split())
        reading_time = round(word_count / 200, 2)

        query = blogs.insert().values(
            title=payload.title,
            slug=payload.slug,
            excerpt=payload.excerpt,
            content=payload.content,
            author=payload.author,
            categories=json.dumps(payload.categories or []),
            tags=json.dumps(payload.tags or []),
            image_url=payload.image_url,
            image_alt=payload.image_alt,
            featured=payload.featured,
            meta_title=payload.meta_title,
            meta_description=payload.meta_description,
            canonical_url=payload.canonical_url,
            og_title=payload.og_title,
            og_description=payload.og_description,
            og_image_url=payload.og_image_url,
            og_image_alt=payload.og_image_alt,
            word_count=word_count,
            reading_time=reading_time,
            published=payload.published,
            publish_at=payload.publish_at,
        )
        blog_id = database.execute(query)

        # Insert blog-tag relationships
        if payload.tags:
            for tag_id in payload.tags:
                database.execute(
                    blog_tags.insert().values(blog_id=blog_id, tag_id=tag_id)
                )

        return {"id": blog_id, "message": "Blog post created successfully", "word_count": word_count, "reading_time": reading_time}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating blog: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create blog: {str(e)}")


@router.get('/admin/blogs/{blog_id}', dependencies=[Depends(require_admin)])
def get_blog(blog_id: int):
    """Get a specific blog post."""
    query = blogs.select().where(blogs.c.id == blog_id)
    blog = database.fetch_one(query)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return dict(blog)


@router.put('/admin/blogs/{blog_id}', dependencies=[Depends(require_admin)])
def update_blog(blog_id: int, payload: BlogUpdate):
    """Update a blog post."""
    # Check if blog exists
    check_query = blogs.select().where(blogs.c.id == blog_id)
    existing = database.fetch_one(check_query)
    if not existing:
        raise HTTPException(status_code=404, detail="Blog post not found")

    # Validate publish_at is in the future if provided
    if payload.publish_at and payload.publish_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Publish date must be in the future")

    # Slug uniqueness check (if updating slug)
    if payload.slug:
        existing_slug = database.fetch_one(blogs.select().where(blogs.c.slug == payload.slug).where(blogs.c.id != blog_id))
        if existing_slug:
            raise HTTPException(status_code=400, detail="Slug already exists. Please choose a unique slug.")

    # Word count and reading time
    import re
    text_content = re.sub('<[^<]+?>', '', payload.content or existing.get('content', ''))
    word_count = len(text_content.split())
    reading_time = round(word_count / 200, 2)

    # Build update values
    update_values = {}
    for k, v in payload.dict(exclude_unset=True).items():
        if k == 'tags' and v is not None:
            update_values['tags'] = json.dumps(v)
            # Update blog_tags junction table
            database.execute(blog_tags.delete().where(blog_tags.c.blog_id == blog_id))
            for tag_id in v:
                database.execute(
                    blog_tags.insert().values(blog_id=blog_id, tag_id=tag_id)
                )
        elif k == 'categories' and v is not None:
            update_values['categories'] = json.dumps(v)
        elif v is not None:
            update_values[k] = v
    update_values['word_count'] = word_count
    update_values['reading_time'] = reading_time

    if not update_values:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = blogs.update().where(blogs.c.id == blog_id).values(**update_values)
    database.execute(query)
    return {"message": "Blog post updated successfully", "word_count": word_count, "reading_time": reading_time}


@router.delete('/admin/blogs/{blog_id}', dependencies=[Depends(require_admin)])
def delete_blog(blog_id: int):
    """Delete a blog post."""
    # Delete associated blog-tag relationships first
    database.execute(blog_tags.delete().where(blog_tags.c.blog_id == blog_id))
    # Delete the blog
    query = blogs.delete().where(blogs.c.id == blog_id)
    database.execute(query)
    return {"message": "Blog post deleted successfully"}


# ===== Categories Management =====

@router.get('/admin/categories', dependencies=[Depends(require_admin)])
def list_categories():
    """List all categories."""
    query = categories.select().order_by(categories.c.name)
    result = database.fetch_all(query)
    return {
        "categories": [
            {
                "id": c["id"],
                "name": c["name"],
                "slug": c["slug"],
                "description": c["description"],
                "created_at": c["created_at"].isoformat() if c["created_at"] else None,
            }
            for c in result
        ]
    }


@router.post('/admin/categories', dependencies=[Depends(require_admin)])
def create_category(payload: CategoryCreate):
    """Create a new category."""
    # Generate slug from name
    slug = payload.name.lower().replace(' ', '-').replace('&', 'and')
    
    try:
        query = categories.insert().values(
            name=payload.name,
            slug=slug,
            description=payload.description,
        )
        category_id = database.execute(query)
        return {"id": category_id, "message": "Category created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Category already exists")


@router.put('/admin/categories/{category_id}', dependencies=[Depends(require_admin)])
def update_category(category_id: int, payload: CategoryUpdate):
    """Update a category."""
    check_query = categories.select().where(categories.c.id == category_id)
    existing = database.fetch_one(check_query)
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_values = {}
    for k, v in payload.dict(exclude_unset=True).items():
        if v is not None:
            update_values[k] = v
            if k == 'name':
                update_values['slug'] = v.lower().replace(' ', '-').replace('&', 'and')
    
    if not update_values:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    query = categories.update().where(categories.c.id == category_id).values(**update_values)
    database.execute(query)
    return {"message": "Category updated successfully"}


@router.delete('/admin/categories/{category_id}', dependencies=[Depends(require_admin)])
def delete_category(category_id: int):
    """Delete a category."""
    query = categories.delete().where(categories.c.id == category_id)
    database.execute(query)
    return {"message": "Category deleted successfully"}


# ===== Tags Management =====

@router.get('/admin/tags', dependencies=[Depends(require_admin)])
def list_tags():
    """List all tags."""
    query = tags_table.select().order_by(tags_table.c.name)
    result = database.fetch_all(query)
    return {
        "tags": [
            {
                "id": t["id"],
                "name": t["name"],
                "slug": t["slug"],
                "created_at": t["created_at"].isoformat() if t["created_at"] else None,
            }
            for t in result
        ]
    }


@router.post('/admin/tags', dependencies=[Depends(require_admin)])
def create_tag(payload: TagCreate):
    """Create a new tag."""
    # Generate slug from name
    slug = payload.name.lower().replace(' ', '-').replace('&', 'and')
    
    try:
        query = tags_table.insert().values(
            name=payload.name,
            slug=slug,
        )
        tag_id = database.execute(query)
        return {"id": tag_id, "message": "Tag created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Tag already exists")


@router.put('/admin/tags/{tag_id}', dependencies=[Depends(require_admin)])
def update_tag(tag_id: int, payload: TagUpdate):
    """Update a tag."""
    check_query = tags_table.select().where(tags_table.c.id == tag_id)
    existing = database.fetch_one(check_query)
    if not existing:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if not payload.name:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    slug = payload.name.lower().replace(' ', '-').replace('&', 'and')
    query = tags_table.update().where(tags_table.c.id == tag_id).values(
        name=payload.name,
        slug=slug
    )
    database.execute(query)
    return {"message": "Tag updated successfully"}


@router.delete('/admin/tags/{tag_id}', dependencies=[Depends(require_admin)])
def delete_tag(tag_id: int):
    """Delete a tag."""
    # Delete associated blog-tag relationships first
    database.execute(blog_tags.delete().where(blog_tags.c.tag_id == tag_id))
    # Delete the tag
    query = tags_table.delete().where(tags_table.c.id == tag_id)
    database.execute(query)
    return {"message": "Tag deleted successfully"}


# ===== Public Endpoints (No Authentication Required) =====

@router.get('/public/blogs')
def get_public_blogs(
    limit: int = 20,
    offset: int = 0,
):
    """Get published blogs for public display."""
    try:
        query = blogs.select().where(blogs.c.published == True).offset(offset).limit(limit).order_by(blogs.c.created_at.desc())
        result = database.fetch_all(query)
        
        blogs_list = []
        for b in result:
            # Safely parse JSON fields
            try:
                categories = json.loads(b.get("categories")) if b.get("categories") and b.get("categories") != "" else []
            except (json.JSONDecodeError, TypeError):
                categories = []
            
            try:
                tags = json.loads(b.get("tags")) if b.get("tags") and b.get("tags") != "" else []
            except (json.JSONDecodeError, TypeError):
                tags = []
            
            blog_dict = {
                "id": b["id"],
                "title": b["title"],
                "slug": b.get("slug", ""),
                "excerpt": b.get("excerpt", ""),
                "content": b.get("content", ""),
                "author": b.get("author", ""),
                "category": b.get("category", ""),
                "categories": categories,
                "tags": tags,
                "image_url": b.get("image_url"),
                "image_alt": b.get("image_alt"),
                "featured": b.get("featured", False),
                "meta_title": b.get("meta_title"),
                "meta_description": b.get("meta_description"),
                "canonical_url": b.get("canonical_url"),
                "og_title": b.get("og_title"),
                "og_description": b.get("og_description"),
                "og_image_url": b.get("og_image_url"),
                "og_image_alt": b.get("og_image_alt"),
                "word_count": b.get("word_count", 0),
                "reading_time": b.get("reading_time", 0.0),
                "published": b.get("published", False),
                "created_at": b["created_at"].isoformat() if b.get("created_at") else None,
                "updated_at": b["updated_at"].isoformat() if b.get("updated_at") else None,
            }
            blogs_list.append(blog_dict)
        
        # Get total count
        count_query = blogs.select().where(blogs.c.published == True)
        total = len(database.fetch_all(count_query))
        
        return {"blogs": blogs_list, "total": total}
    except Exception as e:
        logger.error(f"Error fetching public blogs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching blogs: {str(e)}")


@router.get('/public/blogs/{slug}')
def get_public_blog_by_slug(slug: str):
    """Get a single published blog by slug."""
    try:
        query = blogs.select().where(blogs.c.slug == slug).where(blogs.c.published == True)
        result = database.fetch_one(query)
        
        if not result:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        b = result
        
        # Safely parse JSON fields
        try:
            categories = json.loads(b.get("categories")) if b.get("categories") and b.get("categories") != "" else []
        except (json.JSONDecodeError, TypeError):
            categories = []
        
        try:
            tags = json.loads(b.get("tags")) if b.get("tags") and b.get("tags") != "" else []
        except (json.JSONDecodeError, TypeError):
            tags = []
        
        blog_dict = {
            "id": b["id"],
            "title": b["title"],
            "slug": b.get("slug", ""),
            "excerpt": b.get("excerpt", ""),
            "content": b.get("content", ""),
            "author": b.get("author", ""),
            "category": b.get("category", ""),
            "categories": categories,
            "tags": tags,
            "image_url": b.get("image_url"),
            "image_alt": b.get("image_alt"),
            "featured": b.get("featured", False),
            "meta_title": b.get("meta_title"),
            "meta_description": b.get("meta_description"),
            "canonical_url": b.get("canonical_url"),
            "og_title": b.get("og_title"),
            "og_description": b.get("og_description"),
            "og_image_url": b.get("og_image_url"),
            "og_image_alt": b.get("og_image_alt"),
            "word_count": b.get("word_count", 0),
            "reading_time": b.get("reading_time", 0.0),
            "published": b.get("published", False),
            "created_at": b["created_at"].isoformat() if b.get("created_at") else None,
            "updated_at": b["updated_at"].isoformat() if b.get("updated_at") else None,
        }
        
        return blog_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching public blog by slug: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching blog: {str(e)}")


@router.get('/public/courses')
def get_public_courses(
    limit: int = 20,
    offset: int = 0,
):
    """Get published courses for public display."""
    query = courses.select().where(courses.c.published == True).offset(offset).limit(limit).order_by(courses.c.created_at.desc())
    result = database.fetch_all(query)
    
    courses_list = []
    for c in result:
        course_dict = {
            "id": c["id"],
            "title": c["title"],
            "description": c["description"],
            "instructor": c["instructor"],
            "duration": c["duration"],
            "level": c["level"],
            "price": c["price"],
            "category": c["category"],
            "image_url": c.get("image_url"),
            "published": c["published"],
            "created_at": c["created_at"].isoformat() if c.get("created_at") else None,
            "updated_at": c["updated_at"].isoformat() if c.get("updated_at") else None,
        }
        courses_list.append(course_dict)
    
    # Get total count
    count_query = courses.select().where(courses.c.published == True)
    total = len(database.fetch_all(count_query))
    
    return {"courses": courses_list, "total": total}


@router.get('/public/courses/{course_id}')
def get_public_course(course_id: int):
    """Get a single published course."""
    query = courses.select().where(courses.c.id == course_id).where(courses.c.published == True)
    result = database.fetch_one(query)
    
    if not result:
        raise HTTPException(status_code=404, detail="Course not found")
    
    c = result
    course_dict = {
        "id": c["id"],
        "title": c["title"],
        "description": c["description"],
        "instructor": c["instructor"],
        "duration": c["duration"],
        "level": c["level"],
        "price": c["price"],
        "category": c["category"],
        "image_url": c.get("image_url"),
        "published": c["published"],
        "created_at": c["created_at"].isoformat() if c.get("created_at") else None,
        "updated_at": c["updated_at"].isoformat() if c.get("updated_at") else None,
    }
    
    return course_dict
