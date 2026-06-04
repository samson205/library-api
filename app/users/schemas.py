from typing import Annotated

from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.users.models import BookShelfType
from app.books.schemas import BookRead


class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    password: Annotated[str, Field(..., min_length=8, description="Пароль")]


class UserRead(BaseModel):
    id: Annotated[int, Field(..., description="ID пользователя")]
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    role: Annotated[str, Field(..., description="Роль пользователя")]
    is_active: Annotated[bool, Field(..., description="Активность пользователя")]

    model_config = ConfigDict(from_attributes=True)


class UserBookCreate(BaseModel):
    book_id: Annotated[int, Field(..., description="ID книги")]
    bookshelf_type: Annotated[BookShelfType, Field(BookShelfType.WANT_TO_READ, description="Книжная полка")]


class UserBookRead(BaseModel):
    id: Annotated[int, Field(...)]
    status: Annotated[BookShelfType, Field(...)]
    book: Annotated["BookRead", Field(...)]

    model_config = ConfigDict(from_attributes=True)


class UserLibraryRead(BaseModel):
    bookshelf_type: Annotated[BookShelfType | None, Field(..., description="Книжная полка")]
    books: Annotated[list["UserBookRead"], Field(..., description="Книги на полке")]

    model_config = ConfigDict(from_attributes=True)
