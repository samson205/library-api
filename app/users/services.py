from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.schemas import UserCreate, UserBookCreate
from app.users.models import User, UserBook, BookShelfType
from app.books.models import Book
from app.books.services import BookService
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
            .where(UserBook.id == user_book_id)
        )
        user_book = result.first()
        if not user_book or user_book.book is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found in user library"
            )
        return user_book

    async def get_library(self, user_id: int, bookshelf_type: BookShelfType | None) -> list[UserBook]:
        query = (
            select(UserBook)
            .options(selectinload(UserBook.book).selectinload(Book.authors))
            .options(with_loader_criteria(Book, Book.is_active == True))
            .where(UserBook.user_id == user_id)
        )
        if bookshelf_type is not None:
            query = query.where(UserBook.status == bookshelf_type)

        result = await self.db.scalars(query)
        user_books = result.all()

        return [ub for ub in user_books if ub.book is not None and len(ub.book.authors) > 0]
    
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
        