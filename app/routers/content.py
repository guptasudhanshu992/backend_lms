from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.dependencies import require_admin
from app.services.d1_service import database
from app.models import metadata
from sqlalchemy import Table, Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.sql import func
import json

router = APIRouter()

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

# Define blogs table
blogs = Table(
    "blogs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("excerpt", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("author", String, nullable=False),
    Column("category", String, nullable=False),
    Column("image_url", String, nullable=True),
    Column("published", Boolean, default=False),
    Column("publish_at", DateTime, nullable=True),
    Column("tags", Text, default='[]'),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
)

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
    excerpt: str
    content: str
    author: str
    category: str
    image_url: Optional[str] = None
    published: bool = False
    publish_at: Optional[datetime] = None
    tags: Optional[List[int]] = []


class BlogUpdate(BaseModel):
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    published: Optional[bool] = None
    publish_at: Optional[datetime] = None
    tags: Optional[List[int]] = None


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


# ===== Courses Management =====

@router.get('/courses', dependencies=[Depends(require_admin)])
async def list_courses(
    skip: int = 0,
    limit: int = 100,
):
    """List all courses."""
    query = courses.select().offset(skip).limit(limit).order_by(courses.c.created_at.desc())
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


@router.post('/courses', dependencies=[Depends(require_admin)])
async def create_course(payload: CourseCreate):
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
    course_id = await database.execute(query)
    return {"id": course_id, "message": "Course created successfully"}


@router.get('/courses/{course_id}', dependencies=[Depends(require_admin)])
async def get_course(course_id: int):
    """Get a specific course."""
    query = courses.select().where(courses.c.id == course_id)
    course = await database.fetch_one(query)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return dict(course)


@router.put('/courses/{course_id}', dependencies=[Depends(require_admin)])
async def update_course(course_id: int, payload: CourseUpdate):
    """Update a course."""
    # Check if course exists
    check_query = courses.select().where(courses.c.id == course_id)
    existing = await database.fetch_one(check_query)
    if not existing:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Build update values
    update_values = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if not update_values:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    query = courses.update().where(courses.c.id == course_id).values(**update_values)
    await database.execute(query)
    return {"message": "Course updated successfully"}


@router.delete('/courses/{course_id}', dependencies=[Depends(require_admin)])
async def delete_course(course_id: int):
    """Delete a course."""
    query = courses.delete().where(courses.c.id == course_id)
    await database.execute(query)
    return {"message": "Course deleted successfully"}


# ===== Blog Management =====

@router.get('/blogs', dependencies=[Depends(require_admin)])
async def list_blogs(
    skip: int = 0,
    limit: int = 100,
):
    """List all blog posts."""
    query = blogs.select().offset(skip).limit(limit).order_by(blogs.c.created_at.desc())
    result = await database.fetch_all(query)
    
    blogs_list = []
    for b in result:
        blog_dict = {
            "id": b["id"],
            "title": b["title"],
            "excerpt": b["excerpt"],
            "content": b["content"],
            "author": b["author"],
            "category": b["category"],
            "image_url": b["image_url"],
            "published": b["published"],
            "created_at": b["created_at"].isoformat() if b["created_at"] else None,
        }
        
        # Handle optional columns that might not exist
        if "publish_at" in b.keys():
            blog_dict["publish_at"] = b["publish_at"].isoformat() if b["publish_at"] else None
        else:
            blog_dict["publish_at"] = None
            
        if "tags" in b.keys() and b["tags"]:
            try:
                blog_dict["tags"] = json.loads(b["tags"]) if isinstance(b["tags"], str) else []
            except:
                blog_dict["tags"] = []
        else:
            blog_dict["tags"] = []
            
        blogs_list.append(blog_dict)
    
    return {"blogs": blogs_list}


@router.post('/blogs', dependencies=[Depends(require_admin)])
async def create_blog(payload: BlogCreate):
    """Create a new blog post."""
    # Validate publish_at is in the future if provided
    if payload.publish_at and payload.publish_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Publish date must be in the future")
    
    query = blogs.insert().values(
        title=payload.title,
        excerpt=payload.excerpt,
        content=payload.content,
        author=payload.author,
        category=payload.category,
        image_url=payload.image_url,
        published=payload.published,
        publish_at=payload.publish_at,
        tags=json.dumps(payload.tags or []),
    )
    blog_id = await database.execute(query)
    
    # Insert blog-tag relationships
    if payload.tags:
        for tag_id in payload.tags:
            await database.execute(
                blog_tags.insert().values(blog_id=blog_id, tag_id=tag_id)
            )
    
    return {"id": blog_id, "message": "Blog post created successfully"}


@router.get('/blogs/{blog_id}', dependencies=[Depends(require_admin)])
async def get_blog(blog_id: int):
    """Get a specific blog post."""
    query = blogs.select().where(blogs.c.id == blog_id)
    blog = await database.fetch_one(query)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return dict(blog)


@router.put('/blogs/{blog_id}', dependencies=[Depends(require_admin)])
async def update_blog(blog_id: int, payload: BlogUpdate):
    """Update a blog post."""
    # Check if blog exists
    check_query = blogs.select().where(blogs.c.id == blog_id)
    existing = await database.fetch_one(check_query)
    if not existing:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Validate publish_at is in the future if provided
    if payload.publish_at and payload.publish_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Publish date must be in the future")
    
    # Build update values
    update_values = {}
    for k, v in payload.dict(exclude_unset=True).items():
        if k == 'tags' and v is not None:
            update_values['tags'] = json.dumps(v)
            # Update blog_tags junction table
            await database.execute(blog_tags.delete().where(blog_tags.c.blog_id == blog_id))
            for tag_id in v:
                await database.execute(
                    blog_tags.insert().values(blog_id=blog_id, tag_id=tag_id)
                )
        elif v is not None:
            update_values[k] = v
    
    if not update_values:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    query = blogs.update().where(blogs.c.id == blog_id).values(**update_values)
    await database.execute(query)
    return {"message": "Blog post updated successfully"}


@router.delete('/blogs/{blog_id}', dependencies=[Depends(require_admin)])
async def delete_blog(blog_id: int):
    """Delete a blog post."""
    # Delete associated blog-tag relationships first
    await database.execute(blog_tags.delete().where(blog_tags.c.blog_id == blog_id))
    # Delete the blog
    query = blogs.delete().where(blogs.c.id == blog_id)
    await database.execute(query)
    return {"message": "Blog post deleted successfully"}


# ===== Categories Management =====

@router.get('/categories', dependencies=[Depends(require_admin)])
async def list_categories():
    """List all categories."""
    query = categories.select().order_by(categories.c.name)
    result = await database.fetch_all(query)
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


@router.post('/categories', dependencies=[Depends(require_admin)])
async def create_category(payload: CategoryCreate):
    """Create a new category."""
    # Generate slug from name
    slug = payload.name.lower().replace(' ', '-').replace('&', 'and')
    
    try:
        query = categories.insert().values(
            name=payload.name,
            slug=slug,
            description=payload.description,
        )
        category_id = await database.execute(query)
        return {"id": category_id, "message": "Category created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Category already exists")


@router.put('/categories/{category_id}', dependencies=[Depends(require_admin)])
async def update_category(category_id: int, payload: CategoryUpdate):
    """Update a category."""
    check_query = categories.select().where(categories.c.id == category_id)
    existing = await database.fetch_one(check_query)
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
    await database.execute(query)
    return {"message": "Category updated successfully"}


@router.delete('/categories/{category_id}', dependencies=[Depends(require_admin)])
async def delete_category(category_id: int):
    """Delete a category."""
    query = categories.delete().where(categories.c.id == category_id)
    await database.execute(query)
    return {"message": "Category deleted successfully"}


# ===== Tags Management =====

@router.get('/tags', dependencies=[Depends(require_admin)])
async def list_tags():
    """List all tags."""
    query = tags_table.select().order_by(tags_table.c.name)
    result = await database.fetch_all(query)
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


@router.post('/tags', dependencies=[Depends(require_admin)])
async def create_tag(payload: TagCreate):
    """Create a new tag."""
    # Generate slug from name
    slug = payload.name.lower().replace(' ', '-').replace('&', 'and')
    
    try:
        query = tags_table.insert().values(
            name=payload.name,
            slug=slug,
        )
        tag_id = await database.execute(query)
        return {"id": tag_id, "message": "Tag created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Tag already exists")


@router.put('/tags/{tag_id}', dependencies=[Depends(require_admin)])
async def update_tag(tag_id: int, payload: TagUpdate):
    """Update a tag."""
    check_query = tags_table.select().where(tags_table.c.id == tag_id)
    existing = await database.fetch_one(check_query)
    if not existing:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if not payload.name:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    slug = payload.name.lower().replace(' ', '-').replace('&', 'and')
    query = tags_table.update().where(tags_table.c.id == tag_id).values(
        name=payload.name,
        slug=slug
    )
    await database.execute(query)
    return {"message": "Tag updated successfully"}


@router.delete('/tags/{tag_id}', dependencies=[Depends(require_admin)])
async def delete_tag(tag_id: int):
    """Delete a tag."""
    # Delete associated blog-tag relationships first
    await database.execute(blog_tags.delete().where(blog_tags.c.tag_id == tag_id))
    # Delete the tag
    query = tags_table.delete().where(tags_table.c.id == tag_id)
    await database.execute(query)
    return {"message": "Tag deleted successfully"}
