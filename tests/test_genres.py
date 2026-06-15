import pytest
import pytest_asyncio
from sqlalchemy import select

from app.genres.models import Genre


@pytest_asyncio.fixture
async def existing_genre(db_session):
    genre = Genre(
        name="parent_genre"
    )
    db_session.add(genre)
    await db_session.flush()
    await db_session.refresh(genre)
    return genre


@pytest.mark.asyncio
async def test_create_genre_by_admin_success(client, db_session, admin_headers):
    genre_data = {"name": "Художественная литература"}
    response = await client.post("/genres/", json=genre_data, headers=admin_headers)

    assert response.status_code == 201
    result = await db_session.scalars(
        select(Genre).where(Genre.name == genre_data["name"])
    )
    assert result.first() is not None


@pytest.mark.asyncio
async def test_create_genre_by_regular_user_forbidden(client, user_headers):
    genre_data = {"name": "Художественная литература"}
    response = await client.post("/genres/", json=genre_data, headers=user_headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_genre_by_anonymous_unauthorized(client):
    genre_data = {"name": "Художественная литература"}
    response = await client.post("/genres/", json=genre_data)

    assert response.status_code == 401



@pytest.mark.asyncio
async def test_create_genre_with_parent_success(client, db_session, existing_genre, admin_headers):
    genre_data = {"name": "Художественная литература", "parent_id": existing_genre.id}
    response = await client.post("/genres/", json=genre_data, headers=admin_headers)

    assert response.status_code == 201
    result = await db_session.scalars(
        select(Genre).where(Genre.name == genre_data["name"])
    )
    genre = result.first()
    assert genre is not None
    assert genre.parent_id == existing_genre.id


@pytest.mark.asyncio
async def test_create_genre_with_parent_not_found(client, db_session, admin_headers):
    genre_data = {"name": "Художественная литература", "parent_id": 4}
    response = await client.post("/genres/", json=genre_data, headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Parent genre not found"
    result = await db_session.scalars(
        select(Genre).where(Genre.name == genre_data["name"])
    )
    assert result.first() is None


@pytest.mark.asyncio
async def test_create_genre_with_inactive_parent_not_found(client, db_session, admin_headers):
    parent_genre = Genre(name="inactive_parent", is_active=False)
    db_session.add(parent_genre)
    await db_session.flush()
    await db_session.refresh(parent_genre)

    genre_data = {"name": "genre", "parent_id": parent_genre.id}
    response = await client.post("/genres/", json=genre_data, headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Parent genre not found"
    result = await db_session.scalars(
        select(Genre).where(Genre.name == genre_data["name"])
    )
    assert result.first() is None


@pytest.mark.asyncio
async def test_get_all_genres_success(client, db_session):
    genre1 = Genre(name="first")
    genre2 = Genre(name="second")
    db_session.add_all([genre1, genre2])
    await db_session.flush()

    response = await client.get("/genres/")

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == 2
    assert response_json[0]["name"] == "first"
    assert response_json[1]["name"] == "second"


@pytest.mark.asyncio
async def test_get_all_genres_exluded_inactive(client, db_session):
    genre_active = Genre(name="active")
    genre_inactive = Genre(name="inactive", is_active=False)
    db_session.add_all([genre_active, genre_inactive])
    await db_session.flush()

    response = await client.get("/genres/")

    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["name"] == "active"


@pytest.mark.asyncio
async def test_get_genre_by_id_success(client, existing_genre):
    response = await client.get(f"/genres/{existing_genre.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "parent_genre"


@pytest.mark.asyncio
async def test_get_genre_by_id_not_found(client):
    response = await client.get(f"/genres/101")

    assert response.status_code == 404
    assert response.json()["detail"] == "Genre not found"


@pytest.mark.asyncio
async def test_get_inactive_genre_by_id_not_found(client, db_session):
    genre = Genre(name="inactive", is_active=False)
    db_session.add(genre)
    await db_session.flush()
    await db_session.refresh(genre)

    response = await client.get(f"/genres/{genre.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Genre not found"


@pytest.mark.asyncio
async def test_update_genre_by_admin_success(client, db_session, existing_genre, admin_headers):
    upd_data = {"name": "new_name"}
    response = await client.patch(f"/genres/{existing_genre.id}", json=upd_data, headers=admin_headers)

    assert response.status_code == 200
    await db_session.refresh(existing_genre)
    assert existing_genre.name == upd_data["name"]


@pytest.mark.asyncio
async def test_update_genre_not_found(client, admin_headers):
    upd_data = {"name": "new_name"}
    response = await client.patch("/genres/101", json=upd_data, headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Genre not found"


@pytest.mark.asyncio
async def test_update_genre_by_regular_user_forbidden(client, existing_genre, user_headers):
    upd_data = {"name": "new_name"}
    response = await client.patch(f"/genres/{existing_genre.id}", json=upd_data, headers=user_headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_genre_by_anonymous_unauthorized(client, existing_genre):
    upd_data = {"name": "new_name"}
    response = await client.patch(f"/genres/{existing_genre.id}", json=upd_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_soft_delete_genre_by_admin_success(client, db_session, existing_genre, admin_headers):
    response = await client.delete(f"/genres/{existing_genre.id}", headers=admin_headers)

    assert response.status_code == 204
    await db_session.refresh(existing_genre)
    assert existing_genre.is_active == False


@pytest.mark.asyncio
async def test_soft_delete_genre_not_found(client, admin_headers):
    response = await client.delete("/genres/101", headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Genre not found"


@pytest.mark.asyncio
async def test_soft_delete_already_inactive_genre_not_found(client, db_session, admin_headers):
    genre = Genre(name="inactive", is_active=False)
    db_session.add(genre)
    await db_session.flush()
    await db_session.refresh(genre)

    response = await client.delete(f"/genres/{genre.id}", headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Genre not found"


@pytest.mark.asyncio
async def test_soft_delete_genre_by_regular_user_forbidden(client, existing_genre, user_headers):
    response = await client.delete(f"/genres/{existing_genre.id}", headers=user_headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_soft_delete_genre_by_anonymous_unauthorized(client, existing_genre):
    response = await client.delete(f"/genres/{existing_genre.id}")

    assert response.status_code == 401
