from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.schemas import UserCreate
from app.users.models import User
from app.core.security import hash_password, verify_password, create_token, decode_token


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
            hashed_password=hash_password(data.password),
            role=data.role
        )
        self.db.add(user)
        await self.db.commit()
        return user
    
    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.scalars(select(User).where(User.email == email, User.is_active == True))
        return result.first()
    

class AuthService:
    user_service: UserService

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    async def register_new_user(self, data: UserCreate) -> dict:
        user = await self.user_service.create_user(data)
        tokens = await self.create_tokens(data.email, data.password)
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "user": user
        }

    async def create_tokens(self, email: str, password: str) -> dict:
        user = await self.user_service.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        payload = {"sub": user.email, "role": user.role, "id": user.id}
        access_token = create_token(payload, token_type="access")
        refresh_token = create_token(payload, token_type="refresh")
        return {"access_token": access_token, "refresh_token": refresh_token}
    
    async def create_access_token(self, refresh_token: str):
        user = await self._validate_refresh_token(refresh_token)
        new_access_token = create_token({"sub": user.email, "role": user.role, "id": user.id}, "access")
        return {"access_token": new_access_token, "token_type": "bearer"}

    async def create_refresh_token(self, refresh_token: str):
        user = await self._validate_refresh_token(refresh_token)
        new_refresh_token = create_token({"sub": user.email, "role": user.role, "id": user.id}, "refresh")
        return {"refresh_token": new_refresh_token, "token_type": "bearer"}

    async def _validate_refresh_token(self, refresh_token: str) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )
        payload = decode_token(refresh_token, "refresh")
        email: str | None = payload.get("email")
        if not email:
            raise credentials_exception
        user = await self.user_service.get_user_by_email(email)
        if not user:
            raise credentials_exception
        
        return user
