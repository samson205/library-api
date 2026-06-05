from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import PaginationSchema
from app.reviews.schemas import ReviewCreate, ReviewFilters
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
    
    async def get_reviews(self, pagination: PaginationSchema, filters_schema: ReviewFilters) ->  dict:
        filters_dict = filters_schema.model_dump(exclude_unset=True, exclude_none=True)
        filters = self._build_filters(**filters_dict)
        result = await self.db.scalars(
            select(Review)
            .where(*filters)
            .order_by(Review.id)
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
        return {
            "total": await self._get_reviews_count(filters),
            "items": list(result.all())
        }
    
    async def _get_avg_rating(self, book_id: int) -> float:
        result = await self.db.scalars(
            select(func.avg(Review.grade))
            .where(Review.book_id == book_id)
        )

        avg_rating = result.first() or 0.0
        return avg_rating
    
    async def _get_reviews_count(self, filters: list) -> int:
        result = await self.db.scalar(select(func.count(Review.id)).where(*filters))
        return result or 0
    
    def _build_filters(self, **kwargs) -> list:
        filters = []

        if kwargs.get("user_id"):
            filters.append(Review.user_id == kwargs["user_id"])
        if kwargs.get("book_id"):
            filters.append(Review.book_id == kwargs["book_id"])

        return filters
    