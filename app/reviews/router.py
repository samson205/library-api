from fastapi import APIRouter, status, Depends

from app.users.models import User
from app.users.dependencies import get_current_user
from app.reviews.schemas import ReviewCreate, ReviewRead
from app.reviews.services import ReviewService
from app.reviews.dependencies import get_review_service

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ReviewRead)
async def create_review(
    data: ReviewCreate,
    user: User = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service)
):
    result = await service.create_review(data, user.id)
    return result


@router.get("/{book_id}", response_model=list[ReviewRead])
async def get_reviews_by_book_id(
    book_id: int,
    service: ReviewService = Depends(get_review_service)
):
    result = await service.get_reviews_by_book_id(book_id)
    return result
