from fastapi import APIRouter, Depends

from app.authors.schemas import AuthorRead, AuthorCreate
from app.authors.services import AuthorService
from app.authors.dependencies import get_author_service
from app.users.models import User
from app.users.dependencies import get_current_admin

router = APIRouter(prefix="/authors", tags=["authors"])


@router.post("/", response_model=AuthorRead)
async def create_author(
    data: AuthorCreate,
    admin: User = Depends(get_current_admin),
    service: AuthorService = Depends(get_author_service)
):
    result = await service.create_author(data)
    return result


@router.get("/", response_model=list[AuthorRead])
async def get_all_authors(
    service: AuthorService = Depends(get_author_service)
):
    result = await service.get_all_authors()
    return result
