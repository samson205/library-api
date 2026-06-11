from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.schemas import UserCreate
from app.users.models import User
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
        
        try:
            user = User(
                email=data.email,
                hashed_password=hash_password(data.password)
            )
            self.db.add(user)
            await self.db.commit()
        except Exception:
            await self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        await self.db.refresh(user)
        return user
    
    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.scalars(select(User).where(User.email == email, User.is_active == True))
        return result.first()
