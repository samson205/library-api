from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.users.schemas import UserCreate
from app.auth.schemas import RegisterResponse, RefreshTokenRequest
from app.auth.services import AuthService
from app.auth.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse)
async def create_user(
    data: UserCreate, service: AuthService = Depends(get_auth_service)
):
    return await service.register_new_user(data)


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    return await service.create_tokens(form_data.username, form_data.password)


@router.post("/access-token")
async def access_token(
    data: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)
):
    return await service.create_access_token(data.refresh_token)


@router.post("/refresh-token")
async def refresh_token(
    data: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)
):
    return await service.create_refresh_token(data.refresh_token)
