from fastapi import APIRouter, Depends, UploadFile, File, status

from app.users.services import UserService
from app.users.schemas import UserRead
from app.users.models import User
from app.users.dependencies import get_current_user, get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/me/image", response_model=UserRead)
async def load_user_avatar(
    user: User = Depends(get_current_user),
    image: UploadFile = File(...),
    service: UserService = Depends(get_user_service)
):
    return await service.load_user_avatar(user.id, image)


@router.delete("/me/image", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_avatar(
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    await service.delete_user_avatar(user.id)
    