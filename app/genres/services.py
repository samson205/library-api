from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.genres.schemas import GenreCreate, GenreUpdate
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
                    detail="Parent genre not found",
                )

        genre = Genre(**data.model_dump())
        self.db.add(genre)
        await self.db.commit()
        await self.db.refresh(genre)
        return genre

    async def get_all_genres(self) -> list[Genre]:
        result = await self.db.scalars(select(Genre).where(Genre.is_active == True))
        return list(result.all())

    async def get_genre_by_id(self, genre_id: int) -> Genre:
        result = await self.db.scalars(
            select(Genre).where(Genre.id == genre_id, Genre.is_active == True)
        )
        genre = result.first()
        if not genre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found"
            )
        return genre

    async def update_genre(self, data: GenreUpdate, genre_id: int) -> Genre:
        upd_data = data.model_dump(exclude_unset=True)
        genre = await self.get_genre_by_id(genre_id)

        if upd_data.get("parent_id") is not None:
            result = await self.db.scalars(
                select(Genre).where(Genre.id == data.parent_id, Genre.is_active == True)
            )
            if not result.first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent genre not found",
                )

        for key, value in upd_data.items():
            setattr(genre, key, value)

        await self.db.commit()
        await self.db.refresh(genre)
        return genre

    async def soft_delete_genre(self, genre_id: int) -> None:
        genre = await self.get_genre_by_id(genre_id)
        genre.is_active = False
        await self.db.commit()
