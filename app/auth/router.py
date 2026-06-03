from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.users.schemas import UserCreate
from app.auth.schemas import RegisterResponse
from app.auth.services import AuthService
from app.auth.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse)
async def create_user(
    data: UserCreate,
    service: AuthService = Depends(get_auth_service)
):
    result = await service.register_new_user(data)
    return result


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    result = await service.create_tokens(form_data.username, form_data.password)
    return result
