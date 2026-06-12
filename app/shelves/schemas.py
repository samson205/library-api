from typing import Annotated
from datetime import datetime

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field

from app.core.schemas import BaseList
from app.books.schemas import BookShortRead


class ShelfCreate(BaseModel):
    title: Annotated[str, Field(..., max_length=100, description="Название полки")]
    is_private: Annotated[bool, Field(default=False, description="Приватность полки")]

    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(...)],
        is_private: Annotated[bool, Form(...)]
    ) -> "ShelfCreate":
        return cls(
            title=title,
            is_private=is_private
        )


class ShelfReadBase(BaseModel):
    id: Annotated[int, Field(..., description="ID полки")]
    title: Annotated[str, Field(..., description="Название книги")]
    is_private: Annotated[bool, Field(..., description="Приватность полки")]
    user_id: Annotated[int, Field(..., description="ID пользователя")]
    image_url: Annotated[str | None, Field(..., description="URL изображения полки")]
    created_at: Annotated[datetime, Field(..., description="Дата и время создания полки")]
    books_count: Annotated[int, Field(..., description="Кол-во книг на полке")]

    model_config = ConfigDict(from_attributes=True)


class ShelfRead(ShelfReadBase):
    books: Annotated[list["BookShortRead"], Field(..., description="Книги на полке")]


class ShelfList(BaseList):
    items: Annotated[list["ShelfReadBase"], Field(..., description="Книжные полки")]


class ShelfFilters(BaseModel):
    user_id: Annotated[int | None, Field(None, description="ID пользователя")]
