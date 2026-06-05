from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ReviewCreate(BaseModel):
    book_id: Annotated[int, Field(..., description="ID книги")]
    comment: Annotated[str | None, Field(None, max_length=200, description="Комментарий к отзыву")]
    grade: Annotated[int, Field(..., ge=1, le=5)]


class ReviewRead(BaseModel):
    id: Annotated[int, Field(..., description="ID отзыва")]
    comment: Annotated[str | None, Field(..., description="Комментарий отзыва")]
    grade: Annotated[int, Field(..., description="Оценка")]
    user_id: Annotated[int, Field(..., description="ID пользователя, оставившего отзыв")]
    book_id: Annotated[int, Field(..., description="ID книги")]
    created_at: Annotated[datetime, Field(..., description="Дата создания отзыва")]

    model_config = ConfigDict(from_attributes=True)
