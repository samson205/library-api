from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class GenreCreate(BaseModel):
    name: Annotated[str, Field(..., description="Название жанра")]
    parent_id: Annotated[int | None, Field(default=None, description="ID родительского жанра")]


class GenreRead(BaseModel):
    id: Annotated[int, Field(..., description="ID жанра")]
    name: Annotated[str, Field(..., description="Название жанра")]
    parent_id: Annotated[int | None, Field(..., description="ID родительского жанра")]
    is_active: Annotated[bool, Field(..., description="Активность жанра")]

    model_config = ConfigDict(from_attributes=True)
