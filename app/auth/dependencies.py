from fastapi import Depends

from app.auth.services import UserService, AuthService
from app.users.dependencies import get_user_service


async def get_auth_service(user_service: UserService = Depends(get_user_service)):
    return AuthService(user_service)
