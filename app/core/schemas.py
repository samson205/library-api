from typing import Annotated

from pydantic import BaseModel, Field


class PaginationSchema(BaseModel):
    page: Annotated[int, Field(1, ge=1, description="Страница")]
    page_size: Annotated[int, Field(20, ge=1, le=50, description="Кол-во элементов на странице")]
    

class BaseList(BaseModel):
    total: Annotated[int, Field(..., description="Кол-во найденных элементов")]
    page: Annotated[int, Field(..., description="Текущая страница")]
    page_size: Annotated[int, Field(..., description="Кол-во элементов на странице")]
    