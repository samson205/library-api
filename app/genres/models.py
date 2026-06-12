from sqlalchemy import Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("genres.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    parent: Mapped["Genre | None"] = relationship(
        "Genre", back_populates="children", remote_side="Genre.id"
    )
    children: Mapped[list["Genre"]] = relationship("Genre", back_populates="parent")

    books: Mapped[list["Books"]] = relationship("Book", back_populates="genre")  # type: ignore
