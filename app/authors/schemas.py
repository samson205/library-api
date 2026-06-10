from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field


class AuthorCreate(BaseModel):
    first_name: Annotated[str, Field(..., description="Имя автора")]
    last_name: Annotated[str, Field(..., description="Фамилия автора")]
    bio: Annotated[str | None, Field(default=None, max_length=300, description="Биография автора")]

    @classmethod
    def as_form(
        cls,
        first_name: Annotated[str, Form(...)],
        last_name: Annotated[str, Form(...)],
        bio: Annotated[str | None, Form()] = None
    ) -> "AuthorCreate":
        return cls(
            first_name=first_name,
            last_name=last_name,
            bio=bio
        )


class AuthorShortRead(BaseModel):
    id: Annotated[int, Field(..., description="ID автора")]
    first_name: Annotated[str, Field(..., description="Имя автора")]
    last_name: Annotated[str, Field(..., description="Фамилия автора")]

    model_config = ConfigDict(from_attributes=True)


class AuthorRead(AuthorShortRead):
    bio: Annotated[str | None, Field(..., description="Биография автора")]
    image_url: Annotated[str | None, Field(..., description="URL изображения автора")]


class AuthorUpdate(BaseModel):
    first_name: Annotated[str | None, Field(None, description="Имя автора")]
    last_name: Annotated[str | None, Field(None, description="Фамилия автора")]
    bio: Annotated[str | None, Field(None, max_length=300, description="Биография автора")]
