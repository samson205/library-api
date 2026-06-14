from fastapi import APIRouter, status, Depends, UploadFile, File
from fastapi.responses import FileResponse

from app.core.schemas import PaginationSchema
from app.books.schemas import (
    BookCreate,
    BookRead,
    BookUpdate,
    BookList,
    BookFilters,
    BookResponse,
)
from app.books.services import BookService
from app.books.dependencies import get_book_service
from app.users.models import User
from app.users.dependencies import get_current_admin, get_current_user
from app.core.config import settings

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=BookList)
async def get_books(
    pagination: PaginationSchema = Depends(),
    filters: BookFilters = Depends(),
    service: BookService = Depends(get_book_service),
):
    result = await service.get_books(pagination, filters)
    return {
        "total": result["total"],
        "page": pagination.page,
        "page_size": pagination.page_size,
        "items": result["items"],
    }


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreate = Depends(BookCreate.as_form),
    book_file: UploadFile = File(),
    image: UploadFile | None = File(None),
    admin: User = Depends(get_current_admin),
    service: BookService = Depends(get_book_service),
):
    return await service.create_book(data, book_file, image)


@router.get("/{book_id}", response_model=BookRead)
async def get_book(book_id: int, service: BookService = Depends(get_book_service)):
    return await service.get_book_by_id(book_id)


@router.patch("/{book_id}", response_model=BookRead)
async def update_book(
    book_id: int,
    data: BookUpdate,
    admin: User = Depends(get_current_admin),
    service: BookService = Depends(get_book_service),
):
    return await service.update_book(data, book_id)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_book(
    book_id: int,
    admin: User = Depends(get_current_admin),
    service: BookService = Depends(get_book_service),
):
    await service.soft_delete_book(book_id)


@router.get("/{book_id}/read")
async def read_book(
    book_id: int,
    user: User = Depends(get_current_user),
    service: BookService = Depends(get_book_service),
):
    result = await service.get_book_file(book_id)
    return FileResponse(
        settings.STORAGE_ROOT / result.file_path,
        media_type="application/epub+zip",
        filename=f"book_{result.book_id}.epub",
    )


@router.put("/{book_id}/image", response_model=BookRead)
async def update_book_image(
    book_id: int,
    image: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
    service: BookService = Depends(get_book_service),
):
    return await service.update_book_image(book_id, image)


@router.delete("/{book_id}/image", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book_image(
    book_id: int,
    admin: User = Depends(get_current_admin),
    service: BookService = Depends(get_book_service),
):
    await service.delete_book_image(book_id)
