from typing import Annotated

from fastapi import Query, Form
from pydantic import BaseModel, ConfigDict, Field

from app.core.schemas import BaseList
from app.authors.schemas import AuthorShortRead
from app.genres.schemas import GenreShortRead


class BookCreate(BaseModel):
    title: Annotated[str, Field(..., description="Название книги")]
    description: Annotated[
        str | None, Field(default=None, max_length=500, description="Описание книги")
    ]
    genre_id: Annotated[int, Field(..., description="ID жанра")]
    author_ids: Annotated[list[int], Field(..., description="Список ID авторов книги")]

    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(...)],
        genre_id: Annotated[int, Form(...)],
        author_ids: Annotated[list[int], Form(...)],
        description: Annotated[str | None, Form()] = None,
    ) -> "BookCreate":
        return cls(
            title=title,
            description=description,
            genre_id=genre_id,
            author_ids=author_ids,
        )


class BookFileResponse(BaseModel):
    id: Annotated[int, Field(...)]
    file_format: Annotated[str, Field(...)]
    file_size: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class BookShortRead(BaseModel):
    id: Annotated[int, Field(..., description="ID книги")]
    title: Annotated[str, Field(..., description="Название книги")]
    rating: Annotated[float, Field(..., description="Оценка книги")]
    image_url: Annotated[
        str | None, Field(..., description="URL файла с обложкой книги")
    ]
    genre: Annotated["GenreShortRead", Field(..., description="Жанр книги")]
    authors: Annotated[list[AuthorShortRead], Field(..., description="Авторы книги")]

    model_config = ConfigDict(from_attributes=True)


class BookRead(BaseModel):
    id: Annotated[int, Field(..., description="ID книги")]
    title: Annotated[str, Field(..., description="Название книги")]
    description: Annotated[str | None, Field(..., description="Описание книги")]
    rating: Annotated[float, Field(..., description="Оценка книги")]
    image_url: Annotated[
        str | None, Field(..., description="URL файла с обложкой книги")
    ]
    genre: Annotated["GenreShortRead", Field(..., description="Жанр книги")]
    authors: Annotated[list[AuthorShortRead], Field(..., description="Авторы книги")]

    model_config = ConfigDict(from_attributes=True)


class BookResponse(BookRead):
    files: Annotated[list["BookFileResponse"], Field(..., description="Форматы файлов")]


class BookUpdate(BaseModel):
    title: Annotated[str | None, Field(None, description="Новое название книги")]
    description: Annotated[
        str | None, Field(None, max_length=500, description="Новое описание книги")
    ]
    genre_id: Annotated[int | None, Field(None, description="Новый ID жанра")]
    author_ids: Annotated[
        list[int] | None, Field(None, description="Новый список ID авторов книги")
    ]


class BookList(BaseList):
    items: Annotated[list["BookRead"], Field(..., description="Список книг")]


class BookFilters(BaseModel):
    author_ids: Annotated[
        list[int] | None, Field(Query(default=None), description="ID авторов")
    ]
    genre_id: Annotated[int | None, Field(None, description="ID жанра")]
    rating: Annotated[int | None, Field(None, ge=1, le=5, description="Оценка книги")]
