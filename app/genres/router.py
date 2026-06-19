from fastapi import APIRouter, status, Depends, Response

from app.genres.schemas import GenreRead, GenreCreate, GenreUpdate
from app.genres.services import GenreService
from app.genres.dependencies import get_genre_service
from app.users.models import User
from app.users.dependencies import get_current_admin

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("/", response_model=list[GenreRead])
async def get_all_genres(service: GenreService = Depends(get_genre_service)):
    return await service.get_all_genres()


@router.post("/", response_model=GenreRead, status_code=status.HTTP_201_CREATED)
async def create_genre(
    data: GenreCreate,
    admin: User = Depends(get_current_admin),
    service: GenreService = Depends(get_genre_service),
):
    return await service.create_genre(data)


@router.get("/{genre_id}", response_model=GenreRead)
async def get_genre_by_id(
    genre_id: int, service: GenreService = Depends(get_genre_service)
):
    return await service.get_genre_by_id(genre_id)


@router.patch("/{genre_id}", response_model=GenreRead)
async def update_genre(
    genre_id: int,
    data: GenreUpdate,
    admin: User = Depends(get_current_admin),
    service: GenreService = Depends(get_genre_service),
):
    return await service.update_genre(data, genre_id)


@router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_genre(
    genre_id: int,
    admin: User = Depends(get_current_admin),
    service: GenreService = Depends(get_genre_service),
):
    await service.soft_delete_genre(genre_id)
