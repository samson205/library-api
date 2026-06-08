from fastapi import APIRouter, status, Depends

from app.users.models import User
from app.users.dependencies import get_current_user
from app.core.schemas import PaginationSchema
from app.reviews.schemas import ReviewCreate, ReviewRead, ReviewFilters, ReviewList
from app.reviews.services import ReviewService
from app.reviews.dependencies import get_review_service

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=ReviewList)
async def get_reviews(
    pagination: PaginationSchema = Depends(),
    filters: ReviewFilters = Depends(),
    service: ReviewService = Depends(get_review_service)
):
    result = await service.get_reviews(pagination, filters)
    return {
        "total": result["total"],
        "page": pagination.page,
        "page_size": pagination.page_size,
        "items": result["items"]
    }


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ReviewRead)
async def create_review(
    data: ReviewCreate,
    user: User = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service)
):
    result = await service.create_review(data, user.id)
    return result
