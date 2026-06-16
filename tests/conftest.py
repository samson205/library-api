import os

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

from app.core.database import get_db
from app.core.security import hash_password, create_token
from app.core.config import settings
from app.genres.models import Genre
from app.users.models import User
from app.authors.models import Author
from app.books.models import Book
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def mock_media_root(tmp_path, monkeypatch):
    test_media_dir = tmp_path / "media"
    test_media_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        settings.__class__, "MEDIA_ROOT", property(lambda self: test_media_dir)
    )
    yield test_media_dir


@pytest_asyncio.fixture(scope="function")
async def mock_storage_root(tmp_path, monkeypatch):
    test_storage_dir = tmp_path / "storage"
    test_storage_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        settings.__class__, "STORAGE_ROOT", property(lambda self: test_storage_dir)
    )
    yield test_storage_dir


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    old_env_url = os.getenv("DB_URL")
    os.environ["DB_URL"] = settings.TEST_DB_URL
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.TEST_DB_URL)

    import asyncio

    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
    yield
    await asyncio.to_thread(command.downgrade, alembic_cfg, "base")

    if old_env_url:
        os.environ["DB_URL"] = old_env_url
    else:
        os.environ.pop("DB_URL", None)


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(settings.TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.connect() as connection:
        await connection.begin()
        async with async_session(bind=connection) as session:
            await session.begin_nested()
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session):
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    return admin


@pytest_asyncio.fixture
async def regular_user(db_session):
    user = User(
        email="reader@test.com",
        hashed_password=hash_password("reader123"),
        role="reader",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_headers(admin_user):
    payload = {"sub": admin_user.email, "role": admin_user.role, "id": admin_user.id}
    return {"Authorization": f"Bearer {create_token(payload, "access")}"}


@pytest_asyncio.fixture
async def user_headers(regular_user):
    payload = {
        "sub": regular_user.email,
        "role": regular_user.role,
        "id": regular_user.id,
    }
    return {"Authorization": f"Bearer {create_token(payload, "access")}"}


@pytest_asyncio.fixture
async def user_with_img(db_session):
    user = User(
        email="user@test.com",
        hashed_password=hash_password("user_user"),
        role="reader",
        image_url="users/images/avatar.jpg",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_with_img_headers(user_with_img):
    payload = {
        "sub": user_with_img.email,
        "role": user_with_img.role,
        "id": user_with_img.id,
    }
    return {"Authorization": f"Bearer {create_token(payload, "access")}"}


@pytest_asyncio.fixture
async def refresh_token(regular_user):
    payload = {
        "sub": regular_user.email,
        "role": regular_user.role,
        "id": regular_user.id,
    }
    return create_token(payload, "refresh")


@pytest_asyncio.fixture
async def existing_genre(db_session):
    genre = Genre(name="parent_genre")
    db_session.add(genre)
    await db_session.flush()
    await db_session.refresh(genre)
    return genre


@pytest_asyncio.fixture
async def existing_author(db_session):
    author = Author(first_name="first", last_name="last", bio="biography")
    db_session.add(author)
    await db_session.flush()
    return author


@pytest_asyncio.fixture
async def existing_book(existing_author, existing_genre, db_session):
    book = Book(title="Обломов", genre_id=existing_genre.id, authors=[existing_author])
    db_session.add(book)
    await db_session.flush()
    await db_session.refresh(book)
    return book


@pytest_asyncio.fixture
async def another_book(db_session):
    author = Author(first_name="another", last_name="another")
    genre = Genre(name="another_genre")
    db_session.add_all([author, genre])
    await db_session.flush()

    book = Book(title="another", genre_id=genre.id, authors=[author])
    db_session.add(book)
    await db_session.flush()
    await db_session.refresh(book)
    return book
