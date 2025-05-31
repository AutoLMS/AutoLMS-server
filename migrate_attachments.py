import asyncio
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.attachment import Attachment
from app.models.course import Course

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_attachments():
    """Add user_id to existing attachments based on course_id"""
    logger.info("Starting attachment migration")
    
    # Create database engine and session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Get all attachments without user_id
        query = select(Attachment).where(Attachment.user_id.is_(None))
        result = await session.execute(query)
        attachments = result.scalars().all()
        
        logger.info(f"Found {len(attachments)} attachments without user_id")
        
        # Process each attachment
        for attachment in attachments:
            try:
                # Get the course to find the user_id
                course_query = select(Course).where(Course.id == attachment.course_id)
                course_result = await session.execute(course_query)
                course = course_result.scalar_one_or_none()
                
                if course and course.user_id:
                    # Update the attachment with the user_id from the course
                    attachment.user_id = course.user_id
                    session.add(attachment)
                    logger.info(f"Updated attachment {attachment.id} with user_id {course.user_id}")
                else:
                    logger.warning(f"Could not find course or user_id for attachment {attachment.id}")
            except Exception as e:
                logger.error(f"Error updating attachment {attachment.id}: {str(e)}")
        
        # Commit the changes
        await session.commit()
        logger.info("Migration completed")

if __name__ == "__main__":
    asyncio.run(migrate_attachments())