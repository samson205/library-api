from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    password: Annotated[str, Field(..., min_length=8, description="Пароль")]

    @classmethod
    def as_form(
        cls,
        email: Annotated[EmailStr, Form(...)],
        password: Annotated[str, Form(...)]
    ) -> "UserCreate":
        return cls(
            email=email,
            password=password
        )


class UserRead(BaseModel):
    id: Annotated[int, Field(..., description="ID пользователя")]
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    role: Annotated[str, Field(..., description="Роль пользователя")]
    image_url: Annotated[str | None, Field(..., description="URL аватарки пользователя")]
    # is_active: Annotated[bool, Field(..., description="Активность пользователя")]

    model_config = ConfigDict(from_attributes=True)
