from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import MEDIA_ROOT, MAX_IMAGE_SIZE, ALLOWED_IMAGE_TYPES
from app.core.services import StorageService
from app.core.schemas import PaginationSchema
from app.books.schemas import BookCreate, BookUpdate, BookFilters
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

    async def create_book(self, data: BookCreate, image: UploadFile | None) -> Book:
        if image and image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPG, PNG, WebP images are allowed"
            )
        found_authors = await self.author_service.get_authors_by_ids(data.author_ids)
        if len(found_authors) != len(data.author_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more of the specified author IDs were not found"
            )
        await self.genre_service.get_genre_by_id(data.genre_id)
        images_path = MEDIA_ROOT / "books" / "images"
        file_name, file_size = await StorageService.save_file(image, images_path, MAX_IMAGE_SIZE) if image else (None, None)
        book = Book(
            title=data.title,
            description=data.description,
            genre_id=data.genre_id,
            authors=found_authors,
            image_url=f"/books/images/{file_name}"
        )
        self.db.add(book)
        await self.db.commit()
        new_book = await self.get_book_by_id(book.id)
        return new_book

    async def get_books(self, pagination: PaginationSchema, filters_schema: BookFilters) -> dict:
        filters = self._build_filters(**filters_schema.model_dump(exclude_unset=True, exclude_none=True))
        result = await self.db.scalars(
            select(Book)
            .options(selectinload(Book.authors))
            .options(with_loader_criteria(Author, Author.is_active == True))
            .where(*filters)
            .order_by(Book.id)
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
        items = list(result.unique().all())
        total = await self._get_count_books(filters)
        return {
            "total": total,
            "items": items
        }
    
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

    async def _get_count_books(self, filters: list) -> int:
        result = await self.db.scalar(
            select(func.count(Book.id))
            .where(*filters)
        )
        return result or 0

    def _build_filters(self, **kwargs) -> list:
        filters = [Book.is_active == True, Book.authors.any(Author.is_active == True)]

        if kwargs.get("genre_id"):
            filters.append(Book.genre_id == kwargs["genre_id"])
        if kwargs.get("rating"):
            filters.append(Book.rating >= kwargs["rating"])
        if kwargs.get("author_id"):
            filters.append(
                Book.authors.any(
                    (Author.id.in_(kwargs["author_id"])) &
                    (Author.is_active == True)
                )
            )

        return filters