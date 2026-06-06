from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app.core.schemas import BaseList
from app.authors.schemas import AuthorShortRead


class BookCreate(BaseModel):
    title: Annotated[str, Field(..., description="Название книги")]
    description: Annotated[str | None, Field(default=None, max_length=500, description="Описание книги")]
    genre_id: Annotated[int, Field(..., description="ID жанра")]
    authors_ids: Annotated[list[int], Field(..., description="Список ID авторов книги")]


class BookRead(BaseModel):
    id: Annotated[int, Field(..., description="ID книги")]
    title: Annotated[str, Field(..., description="Название книги")]
    description: Annotated[str | None, Field(..., description="Описание книги")]
    rating: Annotated[float, Field(..., description="Оценка книги")]
    genre_id: Annotated[int, Field(..., description="ID жанра")]
    authors: Annotated[list[AuthorShortRead], Field(..., description="Авторы книги")]

    model_config = ConfigDict(from_attributes=True)


class BookUpdate(BaseModel):
    title: Annotated[str | None, Field(None, description="Новое название книги")]
    description: Annotated[str | None, Field(None, max_length=500, description="Новое описание книги")]
    genre_id: Annotated[int | None, Field(None, description="Новый ID жанра")]
    authors_ids: Annotated[list[int] | None, Field(None, description="Новый список ID авторов книги")]


class BookList(BaseList):
    items: Annotated[list["BookRead"], Field(..., description="Список книг")]


class BookFilters(BaseModel):
    # book_id: Annotated[int | None, Field(..., description="ID книги")]
    author_id: Annotated[list[int] | None, Field(Query(default=None), description="ID авторов")]
    genre_id: Annotated[int | None, Field(None, description="ID жанра")]
    rating: Annotated[int | None, Field(None, ge=1, le=5, description="Оценка книги")]
