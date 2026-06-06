from typing import Annotated

from fastapi import APIRouter, status, Depends, Query

from app.core.schemas import PaginationSchema
from app.books.schemas import BookCreate, BookRead, BookUpdate, BookList, BookFilters
from app.books.services import BookService
from app.books.dependencies import get_book_service
from app.users.models import User
from app.users.dependencies import get_current_admin

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=BookList)
async def get_books(
    pagination: PaginationSchema = Depends(),
    filters: BookFilters = Depends(),
    service: BookService = Depends(get_book_service)
):
    result = await service.get_books(pagination, filters)
    return {
        "total": result["total"],
        "page": pagination.page,
        "page_size": pagination.page_size,
        "items": result["items"]
    }


@router.post("/", response_model=BookRead, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreate,
    admin: User = Depends(get_current_admin),
    service: BookService = Depends(get_book_service)
):
    result = await service.create_book(data)
    return result


@router.put("/{book_id}", response_model=BookRead)
async def update_book(
    book_id: int,
    data: BookUpdate,
    admin: User = Depends(get_current_admin),
    service: BookService = Depends(get_book_service)
):
    result = await service.update_book(data, book_id)
    return result


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_book(
    book_id: int,
    admin: User = Depends(get_current_admin),
    service: BookService = Depends(get_book_service)
):
    await service.soft_delete_book(book_id)
