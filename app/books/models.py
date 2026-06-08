from sqlalchemy import Integer, String, Text, Float, Boolean, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shelves.models import shelf_books


book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True)
)


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(Float, server_default="0")
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    genre: Mapped["Genre"] = relationship("Genre", uselist=False, back_populates="books") # type: ignore
    authors: Mapped[list["Author"]] = relationship(back_populates="books", secondary=book_authors) # type: ignore
    reviews: Mapped[list["Review"]] = relationship("Review", uselist=True, back_populates="book") # type: ignore
    shelves: Mapped[list["Shelf"]] = relationship("Shelf", secondary=shelf_books, back_populates="books") # type: ignore
