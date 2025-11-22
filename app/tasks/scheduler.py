"""
Background task scheduler for automated blog publishing
"""
import asyncio
from datetime import datetime
from app.services.d1_service import database
from app.routers.content import blogs
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_publish_scheduled_blogs():
    """
    Check for blogs with publish_at datetime that has passed
    and automatically publish them
    """
    try:
        # Check if publish_at column exists first
        try:
            # Find blogs that are not published but have a publish_at time that has passed
            query = blogs.select().where(
                (blogs.c.published == False) &
                (blogs.c.publish_at != None) &
                (blogs.c.publish_at <= datetime.utcnow())
            )
            
            scheduled_blogs = await database.fetch_all(query)
            
            for blog in scheduled_blogs:
                # Update blog to published
                update_query = blogs.update().where(blogs.c.id == blog['id']).values(published=True)
                await database.execute(update_query)
                logger.info(f"Auto-published blog: {blog['title']} (ID: {blog['id']})")
            
            if scheduled_blogs:
                logger.info(f"Published {len(scheduled_blogs)} scheduled blog(s)")
        except Exception as column_error:
            if "no such column" in str(column_error).lower():
                logger.warning("Blog publish_at column not yet created. Skipping scheduler check.")
            else:
                raise
            
    except Exception as e:
        logger.error(f"Error in scheduled blog publishing: {str(e)}")

async def run_scheduler():
    """
    Run the scheduler continuously, checking every minute
    """
    logger.info("Blog publishing scheduler started")
    while True:
        await check_and_publish_scheduled_blogs()
        # Wait 60 seconds before next check
        await asyncio.sleep(60)

if __name__ == "__main__":
    # Run the scheduler
    asyncio.run(run_scheduler())
