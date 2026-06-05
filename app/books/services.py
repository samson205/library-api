from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.schemas import BookCreate, BookUpdate
from app.books.models import Book
from app.authors.services import AuthorService
from app.authors.models import Author
from app.genres.services import GenreService


class BookService:
    db: AsyncSession
    author_service: AuthorService
    genre_service: GenreService

    def __init__(self, db: AsyncSession, author_service: AuthorService, genre_service: GenreService) -> None:
        self.db = db
        self.author_service = author_service
        self.genre_service = genre_service

    async def create_book(self, data: BookCreate) -> Book:
        found_authors = await self.author_service.get_authors_by_ids(data.authors_ids)
        if len(found_authors) != len(data.authors_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more of the specified author IDs were not found"
            )
        await self.genre_service.get_genre_by_id(data.genre_id)
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
            .options(with_loader_criteria(Author, Author.is_active == True))
            .where(Book.is_active == True)
        )
        books = result.all()
        return [b for b in books if len(b.authors) > 0]
    
    async def get_book_by_id(self, book_id: int) -> Book:
        result = await self.db.scalars(
            select(Book)
            .options(selectinload(Book.authors))
            .options(with_loader_criteria(Author, Author.is_active == True))
            .where(Book.id == book_id, Book.is_active == True)
        )
        book = result.first()
        if not book or len(book.authors) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found or inactive"
            )
        return book
    
    async def update_book(self, data: BookUpdate, book_id: int) -> Book:
        upd_data = data.model_dump(exclude_unset=True)
        book = await self.get_book_by_id(book_id)
        authors_ids = upd_data.pop("authors_ids", None)
        if authors_ids is not None:
            found_authors = await self.author_service.get_authors_by_ids(authors_ids)
            if len(authors_ids) != len(found_authors):
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more of the specified author IDs were not found"
            )
            setattr(book, "authors", found_authors)
        if upd_data.get("genre_id") is not None:
            await self.genre_service.get_genre_by_id(upd_data["genre_id"])
        
        for key, value in upd_data.items():
            setattr(book, key, value)

        await self.db.commit()
        await self.db.refresh(book)
        return book

    async def soft_delete_book(self, book_id: int) -> None:
        book = await self.get_book_by_id(book_id)
        book.is_active = False
        await self.db.commit()
    