from fastapi import HTTPException, status
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.schemas import UserCreate, UserBookCreate, UserBookFilters
from app.users.models import User, UserBook, BookShelfType
from app.books.models import Book
from app.books.services import BookService
from app.authors.models import Author
from app.core.schemas import PaginationSchema
from app.core.security import hash_password


class UserService:
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, data: UserCreate) -> User:
        result = await self.db.scalars(select(User).where(User.email == data.email, User.is_active == True))
        if result.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password)
        )
        self.db.add(user)
        await self.db.commit()
        return user
    
    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.scalars(select(User).where(User.email == email, User.is_active == True))
        return result.first()


class UserBookService:
    db: AsyncSession
    book_service: BookService

    def __init__(self, db: AsyncSession, book_service: BookService) -> None:
        self.db = db
        self.book_service = book_service

    async def add_book_to_library(self, data: UserBookCreate, user_id: int) -> UserBook:
        await self.book_service.get_book_by_id(data.book_id)
        result = await self.db.scalars(
            select(UserBook).where(UserBook.book_id == data.book_id, UserBook.user_id == user_id)
        )
        if found_book := result.first():
            found_book.status = data.bookshelf_type
            await self.db.commit()
            return await self.get_user_book_by_id(found_book.id)
        
        user_book = UserBook(
            user_id=user_id,
            book_id=data.book_id,
            status=data.bookshelf_type
        )
        self.db.add(user_book)
        await self.db.commit()
        return await self.get_user_book_by_id(user_book.id)
    
    async def get_user_book_by_id(self, user_book_id: int) -> UserBook:
        result = await self.db.scalars(
            select(UserBook)
            .options(selectinload(UserBook.book).selectinload(Book.authors))
            .options(with_loader_criteria(Book, Book.is_active == True))
            .options(with_loader_criteria(Author, Author.is_active == True))
            .where(UserBook.id == user_book_id)
        )
        user_book = result.first()
        if not user_book or user_book.book is None or not user_book.book.authors:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found in user library"
            )
        return user_book

    async def get_library(
        self,
        user_id: int,
        pagination: PaginationSchema, 
        filters_schema: UserBookFilters
    ) -> dict:
        filters = self._build_filters(user_id, **filters_schema.model_dump(exclude_unset=True, exclude_none=True))
        query = (
            select(UserBook)
            .join(UserBook.book)
            .join(Book.authors)
            .options(selectinload(UserBook.book).selectinload(Book.authors))
            .options(with_loader_criteria(Author, Author.is_active == True))
            .where(*filters)
            .order_by(UserBook.id)
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )

        result = await self.db.scalars(query)
        total = await self._get_user_books_count(filters)

        return {
            "total": total,
            "items": result.unique().all()
        }
    
    async def remove_book_from_library(self, book_id: int, user_id: int) -> None:
        result = await self.db.scalars(
            select(UserBook)
            .where(UserBook.book_id == book_id, UserBook.user_id == user_id)
        )
        user_book = result.first()
        if not user_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found in your library"
            )
        
        await self.db.delete(user_book)
        await self.db.commit()

    async def _get_user_books_count(self, filters: list) -> int:
        result = await self.db.scalar(
            select(func.count(distinct(UserBook.id)))
            .join(UserBook.book)
            .join(Book.authors)
            .where(*filters)
        )
        return result or 0

    def _build_filters(self, user_id: int, **kwargs) -> list:
        filters = [
            UserBook.user_id == user_id,
            Book.is_active == True,
            Author.is_active == True
        ]

        if kwargs.get("bookshelf_type"):
            filters.append(UserBook.status == kwargs["bookshelf_type"])
        
        return filters
        