from fastapi import APIRouter, status, Depends, Response

from app.genres.schemas import GenreRead, GenreCreate, GenreUpdate
from app.genres.services import GenreService
from app.genres.dependencies import get_genre_service
from app.users.models import User
from app.users.dependencies import get_current_admin

router = APIRouter(prefix="/genres", tags=["genres"])


@router.post("/", response_model=GenreRead, status_code=status.HTTP_201_CREATED)
async def create_genre(
    data: GenreCreate,
    admin: User = Depends(get_current_admin),
    service: GenreService = Depends(get_genre_service)
):
    result = await service.create_genre(data)
    return result


@router.get("/", response_model=list[GenreRead])
async def get_all_genres(
    service: GenreService = Depends(get_genre_service)
):
    result = await service.get_all_genres()
    return result


@router.put("/{genre_id}", response_model=GenreRead)
async def update_genre(
    genre_id: int,
    data: GenreUpdate,
    admin: User = Depends(get_current_admin),
    service: GenreService = Depends(get_genre_service)
):
    result = await service.update_genre(data, genre_id)
    return result


@router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_genre(
    genre_id: int,
    admin: User = Depends(get_current_admin),
    service: GenreService = Depends(get_genre_service)
):
    await service.soft_delete_genre(genre_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
