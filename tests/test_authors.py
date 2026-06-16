import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.config import settings
from app.authors.models import Author


@pytest_asyncio.fixture
async def existing_author(db_session):
    author = Author(first_name="first", last_name="last", bio="biography")
    db_session.add(author)
    await db_session.flush()
    return author


@pytest.mark.asyncio
async def test_create_author_by_admin_success(client, db_session, admin_headers):
    author_data = {
        "first_name": "Михаил",
        "last_name": "Булгаков",
        "bio": "Автор Мастера и Маргариты",
    }
    response = await client.post("/authors/", data=author_data, headers=admin_headers)

    assert response.status_code == 201

    result = await db_session.scalars(
        select(Author).where(
            Author.first_name == "Михаил", Author.last_name == "Булгаков"
        )
    )
    assert result.first() is not None


@pytest.mark.asyncio
async def test_create_author_with_image_by_admin_success(
    client, db_session, admin_headers, mock_media_root
):
    author_data = {
        "first_name": "Михаил",
        "last_name": "Булгаков",
        "bio": "Автор Мастера и Маргариты",
    }
    file_data = {"image": ("image.jpg", b"fake-image-bytes-content", "image/jpeg")}

    response = await client.post(
        "/authors/", data=author_data, files=file_data, headers=admin_headers
    )

    assert response.status_code == 201
    assert "image_url" in response.json()

    result = await db_session.scalars(
        select(Author).where(
            Author.first_name == "Михаил", Author.last_name == "Булгаков"
        )
    )
    author = result.first()
    assert author is not None
    assert author.image_url is not None

    files_in_media = [f for f in mock_media_root.glob("**/*") if f.is_file()]
    assert len(files_in_media) > 0

    saved_file = files_in_media[0]
    assert saved_file.is_file()
    assert saved_file.stat().st_size > 0


@pytest.mark.asyncio
async def test_create_author_by_regular_user_forbidden(client, user_headers):
    author_data = {"first_name": "Василий", "last_name": "Шукшин"}
    response = await client.post("/authors/", data=author_data, headers=user_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_author_by_anonymous_unauthorized(client):
    author_data = {"first_name": "Аноним", "last_name": "Аноним"}
    response = await client.post("/authors/", data=author_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_all_authors_success(client, db_session):
    author1 = Author(first_name="first_1", last_name="last_1")
    author2 = Author(first_name="first_2", last_name="last_2")
    db_session.add_all([author1, author2])
    await db_session.flush()

    response = await client.get("/authors/")

    assert response.status_code == 200

    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == 2
    assert response_json[0]["first_name"] == "first_1"
    assert response_json[1]["first_name"] == "first_2"


@pytest.mark.asyncio
async def test_get_all_authors_excluded_inactive(client, db_session):
    active_author = Author(first_name="active", last_name="active")
    inactive_author = Author(
        first_name="inactive", last_name="inactive", is_active=False
    )
    db_session.add_all([active_author, inactive_author])
    await db_session.flush()

    response = await client.get("/authors/")
    assert response.status_code == 200

    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["first_name"] == "active"


@pytest.mark.asyncio
async def test_get_author_by_id_success(client, existing_author):
    response = await client.get(f"/authors/{existing_author.id}")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["first_name"] == existing_author.first_name
    assert response_json["last_name"] == existing_author.last_name


@pytest.mark.asyncio
async def test_get_author_by_id_not_found(client):
    response = await client.get(f"/authors/101")

    assert response.status_code == 404
    assert response.json()["detail"] == "Author not found"


@pytest.mark.asyncio
async def test_update_author_by_admin_success(
    client, db_session, existing_author, admin_headers
):
    author_data = {"first_name": "new_first", "last_name": "new_last"}
    response = await client.patch(
        f"/authors/{existing_author.id}", json=author_data, headers=admin_headers
    )

    assert response.status_code == 200

    await db_session.refresh(existing_author)
    assert existing_author.first_name == author_data["first_name"]


@pytest.mark.asyncio
async def test_update_author_by_admin_not_found(client, admin_headers):
    author_data = {"first_name": "new_first", "last_name": "new_last"}
    response = await client.patch(
        "/authors/101", json=author_data, headers=admin_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Author not found"


@pytest.mark.asyncio
async def test_update_author_by_regular_user_forbidden(
    client, existing_author, user_headers
):
    author_data = {"first_name": "new_first", "last_name": "new_last"}
    response = await client.patch(
        f"/authors/{existing_author.id}", json=author_data, headers=user_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_author_by_anonymous_unauthorized(client, existing_author):
    author_data = {"first_name": "new_first", "last_name": "new_last"}
    response = await client.patch(f"/authors/{existing_author.id}", json=author_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_soft_delete_author_by_admin_success(
    client, db_session, existing_author, admin_headers
):
    response = await client.delete(
        f"/authors/{existing_author.id}", headers=admin_headers
    )

    assert response.status_code == 204

    await db_session.refresh(existing_author)
    assert existing_author.is_active == False


@pytest.mark.asyncio
async def test_soft_delete_author_by_regular_user_forbidden(
    client, existing_author, user_headers
):
    response = await client.delete(
        f"/authors/{existing_author.id}", headers=user_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_soft_delete_author_by_anonymous_unauthorized(client, existing_author):
    response = await client.delete(f"/authors/{existing_author.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_author_image_by_admin_success(
    client, db_session, existing_author, admin_headers, mock_media_root
):
    file_data = {"image": ("image.jpg", b"fake-image-bytes-content", "image/jpeg")}
    response = await client.put(
        f"/authors/{existing_author.id}/image", files=file_data, headers=admin_headers
    )

    assert response.status_code == 200

    await db_session.refresh(existing_author)
    assert existing_author.image_url is not None

    files_in_media = [f for f in mock_media_root.glob("**/*") if f.is_file()]
    assert len(files_in_media) > 0

    saved_file = files_in_media[0]
    assert saved_file.is_file()
    assert saved_file.stat().st_size > 0


@pytest.mark.asyncio
async def test_update_author_image_incorrect_type(
    client, existing_author, admin_headers
):
    file_data = {"image": ("image.gif", b"fake-image-bytes-content", "image/gif")}
    response = await client.put(
        f"/authors/{existing_author.id}/image", files=file_data, headers=admin_headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_author_image_too_big(client, existing_author, admin_headers):
    file_data = {
        "image": ("image.jpg", b"0" * (settings.MAX_IMAGE_SIZE + 100), "image/jpeg")
    }
    response = await client.put(
        f"/authors/{existing_author.id}/image", files=file_data, headers=admin_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File is too large"


@pytest.mark.asyncio
async def test_delete_author_image_by_admin_success(
    client, db_session, admin_headers, mock_media_root
):
    author = Author(
        first_name="Лев",
        last_name="Толстой",
        bio="Биография",
        image_url="authors/images/tolstoy.jpg",
    )
    db_session.add(author)
    await db_session.flush()
    await db_session.refresh(author)

    target_dir = mock_media_root / "authors" / "images"
    target_dir.mkdir(parents=True, exist_ok=True)

    fake_image_path = target_dir / "tolstoy.jpg"
    fake_image_path.write_bytes(b"fake-image-bytes-content")
    assert fake_image_path.exists() is True

    response = await client.delete(f"/authors/{author.id}/image", headers=admin_headers)

    assert response.status_code == 204
    assert fake_image_path.exists() is False

    await db_session.refresh(author)
    assert author.image_url is None


@pytest.mark.asyncio
async def test_delete_author_image_missing_on_disk(
    client, db_session, mock_media_root, admin_headers
):
    author = Author(
        first_name="Лев",
        last_name="Толстой",
        bio="Биография",
        image_url="authors/images/tolstoy.jpg",
    )
    db_session.add(author)
    await db_session.flush()
    await db_session.refresh(author)

    assert author.image_url is not None
    assert (mock_media_root / author.image_url).exists() is False

    response = await client.delete(f"/authors/{author.id}/image", headers=admin_headers)

    assert response.status_code == 204

    await db_session.refresh(author)
    assert author.image_url is None
