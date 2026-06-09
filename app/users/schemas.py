from typing import Annotated

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    password: Annotated[str, Field(..., min_length=8, description="Пароль")]


class UserRead(BaseModel):
    id: Annotated[int, Field(..., description="ID пользователя")]
    email: Annotated[EmailStr, Field(..., description="Email пользователя")]
    role: Annotated[str, Field(..., description="Роль пользователя")]
    # is_active: Annotated[bool, Field(..., description="Активность пользователя")]

    model_config = ConfigDict(from_attributes=True)
