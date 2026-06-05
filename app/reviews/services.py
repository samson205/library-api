from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.reviews.schemas import ReviewCreate
from app.reviews.models import Review
from app.books.services import BookService


class ReviewService:
    db: AsyncSession
    book_service: BookService

    def __init__(self, db: AsyncSession, book_service: BookService) -> None:
        self.db = db
        self.book_service = book_service

    async def create_review(self, data: ReviewCreate, user_id: int) -> Review:
        book = await self.book_service.get_book_by_id(data.book_id)
        result = await self.db.scalars(
            select(Review).where(Review.user_id == user_id, Review.book_id == data.book_id)
        )
        if result.first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot leave more than one review per product"
            )
        
        review = Review(**data.model_dump(), user_id=user_id)
        self.db.add(review)
        avg_rating = await self._get_avg_rating(data.book_id)
        book.rating = avg_rating
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def get_reviews_by_book_id(self, book_id: int) -> list[Review]:
        await self.book_service.get_book_by_id(book_id)
        result = await self.db.scalars(
            select(Review)
            .where(Review.book_id == book_id)
        )
        return list(result.all())
    
    async def _get_avg_rating(self, book_id: int) -> float:
        result = await self.db.scalars(
            select(func.avg(Review.grade))
            .where(Review.book_id == book_id)
        )

        avg_rating = result.first() or 0.0
        return avg_rating
    