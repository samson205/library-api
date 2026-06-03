from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

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
    genre_id: Annotated[int, Field(..., description="ID жанра")]
    authors: Annotated[list[AuthorShortRead], Field(..., description="Авторы книги")]

    model_config = ConfigDict(from_attributes=True)
