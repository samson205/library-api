from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(String, default="reader")

    reviews: Mapped[list["Review"]] = relationship( # type: ignore
        back_populates="user",
        cascade="all, delete-orphan"
    )
    shelves: Mapped[list["Shelf"]] = relationship( # type: ignore
        "Shelf",
        back_populates="user",
        cascade="all, delete-orphan"
    )
