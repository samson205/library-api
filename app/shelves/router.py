from fastapi import APIRouter, status, Depends, UploadFile, File

from app.core.schemas import PaginationSchema
from app.shelves.schemas import ShelfRead, ShelfReadBase, ShelfCreate, ShelfFilters, ShelfList
from app.shelves.services import ShelfService
from app.shelves.dependencies import get_shelf_service
from app.users.models import User
from app.users.dependencies import get_current_user, get_current_user_optional

router = APIRouter(prefix="/shelves", tags=["shelves"])


@router.get("/", response_model=ShelfList)
async def get_shelves(
    pagination: PaginationSchema = Depends(),
    filters: ShelfFilters = Depends(),
    user: User | None = Depends(get_current_user_optional),
    service: ShelfService = Depends(get_shelf_service)
):
    user_id = user.id if user else None
    result = await service.get_shelves(user_id, pagination, filters)
    return {
        "total": result["total"],
        "page": pagination.page,
        "page_size": pagination.page_size,
        "items": result["items"]
    }


@router.post("/", response_model=ShelfReadBase, status_code=status.HTTP_201_CREATED)
async def create_shelf(
    data: ShelfCreate = Depends(ShelfCreate.as_form),
    image: UploadFile | None = File(None),
    user: User = Depends(get_current_user),
    service: ShelfService = Depends(get_shelf_service)
):
    return await service.create_shelf(data, user.id, image)


@router.get("/{shelf_id}", response_model=ShelfRead)
async def get_shelf_by_id(
    shelf_id: int,
    user: User | None = Depends(get_current_user_optional),
    service: ShelfService = Depends(get_shelf_service)
):
    user_id = user.id if user else None
    return await service.get_shelf_by_id(shelf_id, user_id)


@router.put("/{shelf_id}/image", response_model=ShelfRead)
async def update_shelf_image(
    shelf_id: int,
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    service: ShelfService = Depends(get_shelf_service)
):
    return await service.update_shelf_image(shelf_id, user, image)


@router.delete("/{shelf_id}/image", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shelf_image(
    shelf_id: int,
    user: User = Depends(get_current_user),
    service: ShelfService = Depends(get_shelf_service)
):
    await service.delete_shelf_image(shelf_id, user)


@router.post("/{shelf_id}/books/{book_id}", status_code=status.HTTP_201_CREATED)
async def add_book_to_shelf(
    shelf_id: int,
    book_id: int,
    user: User = Depends(get_current_user),
    service: ShelfService = Depends(get_shelf_service)
):
    await service.add_book_to_shelf(shelf_id, book_id, user.id)
    return {"detail": "The book has been successfully added to the shelf"}
