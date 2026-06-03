from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.services import BookService
from app.authors.services import AuthorService
from app.authors.dependencies import get_author_service
from app.core.database import get_db


async def get_book_service(
    db: AsyncSession = Depends(get_db),
    author_service: AuthorService = Depends(get_author_service)
) -> BookService:
    return BookService(db, author_service)
