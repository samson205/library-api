import enum

from sqlalchemy import Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BookShelfType(str, enum.Enum):
    WANT_TO_READ = "want_to_read"
    READING = "reading"
    COMPLETED = "completed"


class UserBook(Base):
    __tablename__ = "user_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    status: Mapped[BookShelfType] = mapped_column(
        Enum(BookShelfType, name="bookshelf_type_enum"), 
        default=BookShelfType.WANT_TO_READ,
        nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="library")
    book: Mapped["Book"] = relationship() # type: ignore


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(String, default="reader")

    library: Mapped[list["UserBook"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship( # type: ignore
        back_populates="user",
        cascade="all, delete-orphan"
    )
