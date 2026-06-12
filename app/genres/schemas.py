from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class GenreCreate(BaseModel):
    name: Annotated[str, Field(..., description="Название жанра")]
    parent_id: Annotated[
        int | None, Field(default=None, description="ID родительского жанра")
    ]


class GenreShortRead(BaseModel):
    id: Annotated[int, Field(..., description="ID жанра")]
    name: Annotated[str, Field(..., description="Название жанра")]

    model_config = ConfigDict(from_attributes=True)


class GenreRead(GenreShortRead):
    parent_id: Annotated[int | None, Field(..., description="ID родительского жанра")]


class GenreUpdate(BaseModel):
    name: Annotated[str | None, Field(None, description="Новое название жанра")]
    parent_id: Annotated[
        int | None, Field(None, description="Новый ID родительского жанра")
    ]
