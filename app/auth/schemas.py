from typing import Annotated

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    password: Annotated[str, Field(..., min_length=8, description="Пароль")]
    role: Annotated[str, Field(default="reader", pattern="^(reader|author)$", description="Роль: 'reader' или 'author'")]


class UserRead(BaseModel):
    id: Annotated[int, Field(..., description="ID пользователя")]
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    is_active: Annotated[bool, Field(..., description="Активность пользователя")]
    role: Annotated[str, Field(..., description="Роль пользователя")]

    model_config = ConfigDict(from_attributes=True)


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead

    model_config = ConfigDict(from_attributes=True)