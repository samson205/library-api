from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.books.services import BookService
from app.books.dependencies import get_book_service
from app.reviews.services import ReviewService


async def get_review_service(
    db: AsyncSession = Depends(get_db),
    book_service: BookService = Depends(get_book_service),
) -> ReviewService:
    return ReviewService(db, book_service)
