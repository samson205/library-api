from fastapi import APIRouter, status, Depends, Query

from app.users.schemas import UserBookRead, UserBookCreate, UserLibraryRead, UserRead
from app.users.models import User, BookShelfType
from app.users.dependencies import get_current_user, get_user_book_service
from app.users.services import UserBookService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(
    user: User = Depends(get_current_user)
):
    return user


@router.get("/me/books", response_model=UserLibraryRead)
async def get_user_books(
    user: User = Depends(get_current_user),
    bookshelf_type: BookShelfType | None = Query(None, description="Книжная полка"),
    service: UserBookService = Depends(get_user_book_service)
):
    result = await service.get_library(user.id, bookshelf_type)
    return {
        "bookshelf_type": bookshelf_type,
        "books": result
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
