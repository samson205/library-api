from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.users.models import User
from app.users.services import UserService, UserBookService
from app.books.services import BookService
from app.books.dependencies import get_book_service

oauth2_schema = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


async def get_current_user(
    token: str = Depends(oauth2_schema),
    user_service: UserService = Depends(get_user_service)
) -> User:
    payload = decode_token(token, "access")
    user = await user_service.get_user_by_email(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate access token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def get_current_user_optional(
    token: str = Depends(oauth2_schema),
    user_service: UserService = Depends(get_user_service)
) -> User | None:
    try:
        payload = decode_token(token, "access")
        user = await user_service.get_user_by_email(payload["sub"])
        return user
    except Exception:
        return None


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )
    return user


async def get_user_book_service(
    db: AsyncSession = Depends(get_db),
    book_service: BookService = Depends(get_book_service)
) -> UserBookService:
    return UserBookService(db, book_service)
