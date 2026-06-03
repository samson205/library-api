from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.users.models import User
from app.auth.services import UserService

oauth2_schema = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_schema), db: AsyncSession = Depends(get_db)) -> User:
    payload = decode_token(token, "access")
    result = await db.scalars(
        select(User).where(User.email == payload["sub"], User.is_active == True)
    )
    user = result.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate access token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )
    return user


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)
