from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import MEDIA_ROOT, STORAGE_ROOT, MAX_BOOK_SIZE, ALLOWED_BOOK_EXTENSIONS
from app.core.services import StorageService
from app.core.schemas import PaginationSchema
from app.genres.models import Genre
from app.books.schemas import BookCreate, BookUpdate, BookFilters
from app.books.models import Book, BookFile
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

    async def create_book(self, data: BookCreate, file: UploadFile, image: UploadFile | None) -> Book:
        image_url = await StorageService.save_image(image, "books")

        file_ext = StorageService.get_file_extension(file.filename)
        if file_ext not in ALLOWED_BOOK_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .epub, .fb2, .pdf files are allowed"
            )
        
        found_authors = await self.author_service.get_authors_by_ids(data.author_ids)
        if len(found_authors) != len(data.author_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more of the specified author IDs were not found"
            )
        await self.genre_service.get_genre_by_id(data.genre_id)

        files_path = STORAGE_ROOT / "books" / "files"
        file_name, file_size = await StorageService.save_file(file, files_path, MAX_BOOK_SIZE)

        try:
            book = Book(
                title=data.title,
                description=data.description,
                genre_id=data.genre_id,
                authors=found_authors,
                image_url=image_url
            )
            self.db.add(book)
            await self.db.flush()

            book_file = BookFile(
                book_id=book.id,
                original_filename=file.filename,
                file_path=f"books/files/{file_name}",
                file_size=file_size,
                file_format=file_ext.lstrip(".")
            )
            self.db.add(book_file)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            if image_url:
                StorageService.remove_file(MEDIA_ROOT / image_url)
            if file_name:
                StorageService.remove_file(files_path / file_name)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create book"
            )
        
        new_book = await self.get_book_by_id(book.id)
        return new_book

    async def get_books(self, pagination: PaginationSchema, filters_schema: BookFilters) -> dict:
        filters = self._build_filters(**filters_schema.model_dump(exclude_unset=True, exclude_none=True))
        result = await self.db.scalars(
            select(Book)
            .options(
                selectinload(Book.authors),
                selectinload(Book.genre)
            )
            .options(
                with_loader_criteria(Author, Author.is_active == True),
                with_loader_criteria(Genre, Genre.is_active == True)
            )
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
    
    async def get_book_by_id(self, book_id: int, load_files: bool = False) -> Book:
        stmt = (
            select(Book)
            .options(
                selectinload(Book.authors),
                selectinload(Book.genre)
            )
            .options(
                with_loader_criteria(Author, Author.is_active == True),
                with_loader_criteria(Genre, Genre.is_active == True)
            )
            .where(Book.id == book_id, Book.is_active == True)
        )
        if load_files:
            stmt = stmt.options(selectinload(Book.files))
        result = await self.db.scalars(stmt)
        book = result.first()
        if not book or len(book.authors) == 0 or not book.genre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found or inactive"
            )
        return book
    
    async def get_book_file(self, book_id: int) -> BookFile:
        book = await self.get_book_by_id(book_id, load_files=True)
        file = next(
            (f for f in book.files if f.file_format == "epub"),
            None
        )
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book file not found"
            )
        return file
    
    async def update_book(self, data: BookUpdate, book_id: int) -> Book:
        upd_data = data.model_dump(exclude_unset=True)
        book = await self.get_book_by_id(book_id)
        author_ids = upd_data.pop("author_ids", None)
        if author_ids is not None:
            found_authors = await self.author_service.get_authors_by_ids(author_ids)
            if len(author_ids) != len(found_authors):
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more of the specified author IDs were not found"
            )
            setattr(book, "authors", found_authors)
        if upd_data.get("genre_id") is not None:
            await self.genre_service.get_genre_by_id(upd_data["genre_id"])
        
        for key, value in upd_data.items():
            setattr(book, key, value)

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update book"
            )

        await self.db.refresh(book)
        return book

    async def soft_delete_book(self, book_id: int) -> None:
        book = await self.get_book_by_id(book_id)
        book.is_active = False
        try:
            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to soft delete book"
            )

    async def update_book_image(self, book_id: int, image: UploadFile) -> Book:
        image_url = await StorageService.save_image(image, "books")
        book = await self.get_book_by_id(book_id)
        old_image_url = book.image_url

        try:
            book.image_url = image_url
            await self.db.commit()

        except Exception:
            await self.db.rollback()
            if image_url:
                StorageService.remove_file(MEDIA_ROOT / image_url)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update book image"
            )
        
        if old_image_url:
            StorageService.remove_file(MEDIA_ROOT / old_image_url)
        await self.db.refresh(book)
        return book
    
    async def delete_book_image(self, book_id: int) -> None:
        book = await self.get_book_by_id(book_id)
        image_url = book.image_url
        if not image_url:
            return None
        book.image_url = None

        try:
            await self.db.commit()
            
        except Exception:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete book image"
            )

        if image_url:
            StorageService.remove_file(MEDIA_ROOT / image_url)
        return None

    async def _get_count_books(self, filters: list) -> int:
        result = await self.db.scalar(
            select(func.count(Book.id))
            .where(*filters)
        )
        return result or 0

    def _build_filters(self, **kwargs) -> list:
        filters = [
            Book.is_active == True,
            Book.authors.any(Author.is_active == True),
            Book.genre.has(Genre.is_active == True)
        ]

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
    