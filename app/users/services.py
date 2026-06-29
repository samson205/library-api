import uuid

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.schemas import UserCreate
from app.users.models import User
from app.core.security import hash_password
from app.core.services import StorageService
from app.core.config import settings


class UserService:
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, data: UserCreate) -> User:
        result = await self.db.scalars(
            select(User).where(User.email == data.email, User.is_active == True)
        )
        if result.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )

        try:
            user = User(email=data.email, username=self._generate_username(data.email), hashed_password=hash_password(data.password))
            self.db.add(user)
            await self.db.commit()
        except Exception:
            await self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

        await self.db.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.scalars(
            select(User).where(User.email == email, User.is_active == True)
        )
        return result.first()
    
    async def get_user_by_username(self, username: str) -> User:
        result = await self.db.scalars(
            select(User).where(User.username == username, User.is_active == True)
        )
        user = result.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def get_user_by_id(self, user_id: int) -> User:
        result = await self.db.scalars(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    async def load_user_avatar(self, user_id: int, image: UploadFile) -> User:
        image_url = await StorageService.save_image(image, "users")
        user = await self.get_user_by_id(user_id)
        old_image_url = user.image_url

        try:
            user.image_url = image_url
            await self.db.commit()

        except Exception:
            await self.db.rollback()
            if image_url:
                StorageService.remove_file(settings.MEDIA_ROOT / image_url)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load user avatar",
            )

        if old_image_url:
            StorageService.remove_file(settings.MEDIA_ROOT / old_image_url)

        await self.db.refresh(user)
        return user

    async def delete_user_avatar(self, user_id: int) -> None:
        user = await self.get_user_by_id(user_id)
        image_url = user.image_url
        user.image_url = None

        try:
            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user avatar",
            )

        if image_url:
            StorageService.remove_file(settings.MEDIA_ROOT / image_url)
        return None
    
    @staticmethod
    def _generate_username(email: str) -> str:
        base_name = email.split("@")[0]
        clean_name = "".join([c for c in base_name if c.isalnum() or c in "._"])
        return f"{clean_name}_{uuid.uuid4().hex[:4]}"
