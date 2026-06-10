from datetime import datetime

from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

shelf_books = Table(
    "shelf_books",
    Base.metadata,
    Column("shelf_id", Integer, ForeignKey("shelves.id", ondelete="CASCADE"), primary_key=True),
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
)


class Shelf(Base):
    __tablename__ = "shelves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship( # type: ignore
        "User",
        back_populates="shelves"
    )
    books: Mapped[list["Book"]] = relationship( # type: ignore
        "Book",
        secondary=shelf_books,
        back_populates="shelves"
    )
