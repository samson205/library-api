from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.schemas import BookCreate
from app.books.models import Book
from app.authors.services import AuthorService


class BookService:
    db: AsyncSession
    author_service: AuthorService

    def __init__(self, db: AsyncSession, author_service: AuthorService) -> None:
        self.db = db
        self.author_service = author_service

    async def create_book(self, data: BookCreate) -> Book:
        found_authors = await self.author_service.get_authors_by_ids(data.authors_ids)
        if len(found_authors) != len(data.authors_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more of the specified author IDs were not found"
            )
        book = Book(
            title=data.title,
            description=data.description,
            genre_id=data.genre_id,
            authors=found_authors
        )
        self.db.add(book)
        await self.db.commit()
        new_book = await self.get_book_by_id(book.id)
        return new_book

    async def get_all_books(self) -> list[Book]:
        result = await self.db.scalars(
            select(Book)
            .options(selectinload(Book.authors))
            .where(Book.is_active == True)
        )
        return list(result.unique().all())
    
    async def get_book_by_id(self, book_id: int) -> Book:
        result = await self.db.scalars(
            select(Book)
            .options(selectinload(Book.authors))
            .where(Book.id == book_id, Book.is_active == True)
        )
        book = result.first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        return book
