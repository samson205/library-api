from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ALLOWED_IMAGE_TYPES, MEDIA_ROOT, MAX_IMAGE_SIZE
from app.core.services import StorageService
from app.authors.models import Author
from app.authors.schemas import AuthorCreate, AuthorUpdate


class AuthorService:
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_author(self, data: AuthorCreate, image: UploadFile | None) -> Author:
        if image and image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPG, PNG, WebP images are allowed"
            )
        
        images_path = MEDIA_ROOT / "authors" / "images"
        image_name, _ = await StorageService.save_file(image, images_path, MAX_IMAGE_SIZE) if image else (None, None)
        image_url = f"authors/images/{image_name}" if image_name else None

        try:
            author = Author(**data.model_dump(), image_url=image_url)
            self.db.add(author)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            if image_name:
                StorageService.remove_file(f"{images_path / image_name}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create author"
            )

        await self.db.refresh(author)
        return author
    
    async def get_all_authors(self) -> list[Author]:
        result = await self.db.scalars(
            select(Author).where(Author.is_active == True)
        )
        return list(result.all())
    
    async def get_author_by_id(self, author_id: int) -> Author:
        result = await self.db.scalars(select(Author).where(Author.id == author_id, Author.is_active == True))
        author = result.first()
        if not author:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Author not found"
            )
        return author
    
    async def get_authors_by_ids(self, authors_ids: list[int]) -> list[Author]:
        result = await self.db.scalars(select(Author).where(Author.id.in_(authors_ids), Author.is_active == True))
        return list(result.all())
    
    async def update_author(self, data: AuthorUpdate, author_id: int) -> Author:
        upd_data = data.model_dump(exclude_unset=True)
        author = await self.get_author_by_id(author_id)
        for key, value in upd_data.items():
            setattr(author, key, value)
        await self.db.commit()
        await self.db.refresh(author)
        return author

    async def soft_delete_author(self, author_id: int) -> None:
        author = await self.get_author_by_id(author_id)
        author.is_active = False
        await self.db.commit()
        