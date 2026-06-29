from pydantic import BaseModel, ConfigDict

from app.users.schemas import UserCurrentRead


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserCurrentRead

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    refresh_token: str
