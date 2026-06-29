import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_get_me_success(client, regular_user, user_headers):
    response = await client.get("/users/me", headers=user_headers)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["email"] == regular_user.email
    assert response_json["username"] == regular_user.username
    assert response_json.get("hashed_password", None) is None


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    response = await client.get("/users/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_success(client, regular_user, user_headers):
    upd_data = {"username": "new_username"}
    response = await client.patch("/users/me", json=upd_data, headers=user_headers)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json.get("username") == upd_data["username"]
    assert response_json.get("hashed_password", None) is None


@pytest.mark.asyncio
async def test_update_user_unauthorized(client):
    upd_data = {"username": "new_username"}
    response = await client.patch("/users/me", json=upd_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_incorrect_data(client, regular_user, user_headers):
    upd_data = {"username": "0" * 100}
    response = await client.patch("/users/me", json=upd_data, headers=user_headers)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_username_already_exists(
    client, regular_user, user_with_img, user_headers
):
    upd_data = {"username": "reader_img"}
    response = await client.patch("/users/me", json=upd_data, headers=user_headers)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_user_by_username_success(client, regular_user):
    response = await client.get(f"/users/{regular_user.username}")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json.get("username") == regular_user.username
    assert response_json.get("email") is None
    assert response_json.get("hashed_password") is None


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(client):
    response = await client.get("/users/reader_reader")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_load_user_avatar_success(
    client, db_session, regular_user, user_headers, mock_media_root
):
    file_data = {"image": ("image.jpg", b"fake-image-bytes-content", "image/jpeg")}
    response = await client.put(
        "/users/me/image", files=file_data, headers=user_headers
    )

    assert response.status_code == 200

    await db_session.refresh(regular_user)
    assert regular_user.image_url is not None

    files_in_media = [f for f in mock_media_root.glob("**/*") if f.is_file()]
    assert len(files_in_media) > 0

    saved_file = files_in_media[0]
    assert saved_file.is_file()
    assert saved_file.stat().st_size > 0


@pytest.mark.asyncio
async def test_load_user_avatar_unauthorized(client):
    file_data = {"image": ("image.jpg", b"fake-image-bytes-content", "image/jpeg")}
    response = await client.put("/users/me/image", files=file_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_load_user_avatar_incorrect_type(client, user_headers):
    file_data = {"image": ("image.gif", b"fake-image-bytes-content", "image/gif")}
    response = await client.put(
        "/users/me/image", files=file_data, headers=user_headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_load_user_avatar_image_too_big(client, user_headers):
    file_data = {
        "image": ("image.jpg", b"0" * (settings.MAX_IMAGE_SIZE + 100), "image/jpeg")
    }
    response = await client.put(
        "/users/me/image", files=file_data, headers=user_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File is too large"


@pytest.mark.asyncio
async def test_delete_user_avatar_success(
    client, db_session, user_with_img, user_with_img_headers, mock_media_root
):
    fake_image_path = mock_media_root / user_with_img.image_url
    fake_image_path.parent.mkdir(parents=True, exist_ok=True)
    fake_image_path.write_bytes(b"fake-image-bytes-content")
    assert fake_image_path.exists() == True

    response = await client.delete("/users/me/image", headers=user_with_img_headers)

    assert response.status_code == 204
    assert fake_image_path.exists() == False

    await db_session.refresh(user_with_img)
    assert user_with_img.image_url is None


@pytest.mark.asyncio
async def test_delete_user_avatar_unauthorized(client):
    response = await client.delete("/users/me/image")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_user_avatar_missing_on_disk(
    client, db_session, user_with_img, user_with_img_headers, mock_media_root
):
    assert user_with_img.image_url is not None
    assert (mock_media_root / user_with_img.image_url).exists() == False

    response = await client.delete("/users/me/image", headers=user_with_img_headers)

    assert response.status_code == 204
    await db_session.refresh(user_with_img)
    assert user_with_img.image_url is None
