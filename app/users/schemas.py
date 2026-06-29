import re
from typing import Annotated

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    password: Annotated[str, Field(..., min_length=8, description="Пароль")]


class UserRead(BaseModel):
    id: Annotated[int, Field(..., description="ID пользователя")]
    username: Annotated[str, Field(..., description="Никнейм пользователя")]
    image_url: Annotated[
        str | None, Field(..., description="URL аватарки пользователя")
    ]

    model_config = ConfigDict(from_attributes=True)


class UserCurrentRead(UserRead):
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    role: Annotated[str, Field(..., description="Роль пользователя")]


class UserUpdate(BaseModel):
    username: Annotated[str | None, Field(None, min_length=3, max_length=20)]

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if not re.match(r"^[a-zA-Z0-9._-]+$", value):
            raise ValueError(
                "Username can only contain alphanumeric characters, dots, underscores, and hyphens"
            )
        return value
