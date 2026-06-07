from fastapi import APIRouter, Depends

from app.users.schemas import UserRead
from app.users.models import User
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(
    user: User = Depends(get_current_user)
):
    return user
