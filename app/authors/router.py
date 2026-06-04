from fastapi import APIRouter, status, Depends

from app.authors.schemas import AuthorRead, AuthorCreate, AuthorUpdate
from app.authors.services import AuthorService
from app.authors.dependencies import get_author_service
from app.users.models import User
from app.users.dependencies import get_current_admin

router = APIRouter(prefix="/authors", tags=["authors"])


@router.post("/", response_model=AuthorRead, status_code=status.HTTP_201_CREATED)
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


@router.put("/{author_id}", response_model=AuthorRead)
async def update_author(
    author_id: int,
    data: AuthorUpdate,
    admin: User = Depends(get_current_admin),
    service: AuthorService = Depends(get_author_service)
):
    result = await service.update_author(data, author_id)
    return result
