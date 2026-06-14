from datetime import datetime, timezone, timedelta

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.core.config import settings

if not settings.ALGORITHM or not settings.SECRET_KEY:
    raise Exception

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, token_type: str):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        if token_type == "access"
        else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "token_type": token_type})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, token_type: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Could not validate {token_type} token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str | None = payload.get("sub")
        decoded_token_type: str | None = payload.get("token_type")
        if not email or decoded_token_type != token_type:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    return payload
