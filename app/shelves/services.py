from fastapi import HTTPException, status, UploadFile

from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE, MEDIA_ROOT
from app.core.services import StorageService
from app.core.schemas import PaginationSchema
from app.users.models import User
from app.shelves.schemas import ShelfCreate, ShelfFilters
from app.shelves.models import Shelf
from app.books.models import Book
from app.books.services import BookService
from app.authors.models import Author


class ShelfService:
    db: AsyncSession
    book_service: BookService

    def __init__(self, db: AsyncSession, book_service: BookService) -> None:
        self.db = db
        self.book_service = book_service

    async def create_shelf(self, data: ShelfCreate, user_id: int, image: UploadFile | None) -> Shelf:
        if image and image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPG, PNG, WebP images are allowed"
            )
        
        image_url = await self._save_shelf_image(image)

        try:
            shelf = Shelf(**data.model_dump(), user_id=user_id, image_url=image_url)
            self.db.add(shelf)
            await self.db.commit()
        except Exception:
            await self.db.rollback()

            if image_url:
                StorageService.remove_file(MEDIA_ROOT / image_url)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create shelf"
            )
        
        await self.db.refresh(shelf)
        return shelf
    
    async def get_shelves(self, current_user_id: int | None, pagination: PaginationSchema, filters_schema: ShelfFilters) -> dict:
        filters = self._build_filters(current_user_id, **filters_schema.model_dump(exclude_none=True, exclude_unset=True))
        result = await self.db.scalars(
            select(Shelf)
            .where(*filters)
            .order_by(Shelf.id)
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
        items = list(result.all())
        total = await self._get_count_shelves(filters)
        return {
            "total": total,
            "items": items
        }
    
    async def get_shelf_by_id(self, shelf_id: int, user_id: int | None) -> Shelf:
        result = await self.db.scalars(
            select(Shelf)
            .options(selectinload(Shelf.books).selectinload(Book.authors))
            .options(with_loader_criteria(Book, Book.is_active == True))
            .options(with_loader_criteria(Author, Author.is_active == True))
            .where(
                Shelf.id == shelf_id,
                or_(
                    Shelf.is_private == False,
                    Shelf.user_id == user_id
                )
            )
        )
        shelf = result.first()
        if not shelf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shelf not found"
            )
        return shelf
    
    async def add_book_to_shelf(self, shelf_id: int, book_id: int, user_id: int) -> None:
        result = await self.db.scalars(
            select(Shelf)
            .options(selectinload(Shelf.books))
            .where(Shelf.id == shelf_id, Shelf.user_id == user_id)
        )
        shelf = result.first()
        if not shelf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shelf not found or you don't have access"
            )
        
        book = await self.book_service.get_book_by_id(book_id)
        if book in shelf.books:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book is already on this shelf"
            )
        
        shelf.books.append(book)
        await self.db.commit()

    async def update_shelf_image(self, shelf_id: int, user: User, image: UploadFile) -> Shelf:
        shelf = await self.get_shelf_by_id(shelf_id, user.id)
        if user.id != shelf.user_id and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can change the image of only your own shelf"
            )
        
        old_image_url = shelf.image_url
        image_url = await self._save_shelf_image(image)

        try:
            shelf.image_url = image_url
            await self.db.commit()
        except Exception:
            await self.db.rollback()

            if image_url:
                StorageService.remove_file(MEDIA_ROOT / image_url)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update shelf image"
            )
        
        if old_image_url:
            StorageService.remove_file(MEDIA_ROOT / old_image_url)

        await self.db.refresh(shelf)
        return shelf
    
    async def delete_shelf_image(self, shelf_id: int, user: User) -> None:
        shelf = await self.get_shelf_by_id(shelf_id, user.id)
        if user.id != shelf.user_id and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can delete the image of only your own shelf"
            )
        
        image_url = shelf.image_url
        shelf.image_url = None

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete shelf image"
            )
        
        if image_url:
            StorageService.remove_file(MEDIA_ROOT / image_url)
        return None

    async def _save_shelf_image(self, image: UploadFile | None) -> str | None:
        if not image:
            return None
        images_path = MEDIA_ROOT / "shelves" / "images"
        image_name, _ = await StorageService.save_file(image, images_path, MAX_IMAGE_SIZE)
        image_url = f"shelves/images/{image_name}"
        return image_url
    
    async def _get_count_shelves(self, filters: list) -> int:
        result = await self.db.scalar(
            select(func.count(Shelf.id))
            .where(*filters)
        )
        return result or 0

    def _build_filters(self, current_user_id: int | None, **kwargs) -> list:
        filters = []

        if kwargs.get("user_id"):
            target_user_id = kwargs["user_id"]
            if current_user_id == target_user_id:
                filters.append(Shelf.user_id == target_user_id)
            else:
                filters.append(Shelf.user_id == target_user_id)
                filters.append(Shelf.is_private == False)
        else:
            filters.append(
                or_(
                    Shelf.is_private == False,
                    Shelf.user_id == current_user_id
                )
            )

        return filters
    