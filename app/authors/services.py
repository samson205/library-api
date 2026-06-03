from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authors.models import Author
from app.authors.schemas import AuthorCreate


class AuthorService:
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_author(self, data: AuthorCreate) -> Author:
        author = Author(**data.model_dump())
        self.db.add(author)
        await self.db.commit()
        await self.db.refresh(author)
        return author
    
    async def get_all_authors(self) -> list[Author]:
        result = await self.db.scalars(
            select(Author).where(Author.is_active == True)
        )
        return list(result.all())
    
    async def get_authors_by_ids(self, authors_ids: list[int]) -> list[Author]:
        result = await self.db.scalars(select(Author).where(Author.id.in_(authors_ids), Author.is_active == True))
        return list(result.all())
