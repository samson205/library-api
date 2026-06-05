from fastapi import APIRouter, status, Depends, Query

from app.core.schemas import PaginationSchema
from app.users.schemas import UserBookRead, UserBookCreate, UserLibraryList, UserRead, UserBookFilters
from app.users.models import User
from app.users.dependencies import get_current_user, get_user_book_service
from app.users.services import UserBookService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(
    user: User = Depends(get_current_user)
):
    return user


@router.get("/me/books", response_model=UserLibraryList)
async def get_user_books(
    pagination: PaginationSchema = Depends(),
    filters: UserBookFilters = Depends(),
    user: User = Depends(get_current_user),
    service: UserBookService = Depends(get_user_book_service)
):
    result = await service.get_library(user.id, pagination, filters)
    return {
        "total": result["total"],
        "page": pagination.page,
        "page_size": pagination.page_size,
        "bookshelf_type": filters.bookshelf_type,
        "items": result["items"]
    }


@router.post("/me/books", response_model=UserBookRead)
async def add_book_to_shelf(
    data: UserBookCreate,
    user: User = Depends(get_current_user),
    service: UserBookService = Depends(get_user_book_service)
):
    result = await service.add_book_to_library(data, user.id)
    return result


@router.delete("/me/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book_from_library(
    book_id: int,
    user: User = Depends(get_current_user),
    service: UserBookService = Depends(get_user_book_service)
):
    await service.remove_book_from_library(book_id, user.id)
    return None
