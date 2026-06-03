from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.genres.schemas import GenreCreate
from app.genres.models import Genre


class GenreService:
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_genre(self, data: GenreCreate) -> Genre:
        if data.parent_id:
            result = await self.db.scalars(
                select(Genre).where(Genre.id == data.parent_id, Genre.is_active == True)
            )
            if not result.first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent genre not found"
                )
            
        genre = Genre(**data.model_dump())
        self.db.add(genre)
        await self.db.commit()
        return genre
        
    async def get_all_genres(self) -> list[Genre]:
        result = await self.db.scalars(select(Genre).where(Genre.is_active == True))
        return list(result.all())
