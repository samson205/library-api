from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.genres.services import GenreService


async def get_genre_service(db: AsyncSession = Depends(get_db)):
    return GenreService(db)
