from typing import Annotated

from pydantic import BaseModel, Field, EmailStr, ConfigDict


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
