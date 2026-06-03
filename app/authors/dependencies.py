from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.authors.services import AuthorService


async def get_author_service(db: AsyncSession = Depends(get_db)) -> AuthorService:
    return AuthorService(db)
