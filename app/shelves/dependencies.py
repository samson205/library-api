from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shelves.services import ShelfService
from app.books.services import BookService
from app.books.dependencies import get_book_service


async def get_shelf_service(
    db: AsyncSession = Depends(get_db),
    book_service: BookService = Depends(get_book_service),
) -> ShelfService:
    return ShelfService(db, book_service)
