from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AuthorCreate(BaseModel):
    first_name: Annotated[str, Field(..., description="Имя автора")]
    last_name: Annotated[str, Field(..., description="Фамилия автора")]
    bio: Annotated[str | None, Field(default=None, max_length=300, description="Биография автора")]


class AuthorRead(BaseModel):
    id: Annotated[int, Field(..., description="ID автора")]
    first_name: Annotated[str, Field(..., description="Имя автора")]
    last_name: Annotated[str, Field(..., description="Фамилия автора")]
    bio: Annotated[str | None, Field(..., description="Биография автора")]

    model_config = ConfigDict(from_attributes=True)


class AuthorShortRead(BaseModel):
    id: int
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)
