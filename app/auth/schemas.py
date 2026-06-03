from pydantic import BaseModel, ConfigDict

from app.users.schemas import UserRead


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead

    model_config = ConfigDict(from_attributes=True)