import pytest
import pytest_asyncio

from app.core.config import settings
from app.core.security import hash_password, create_token
from app.users.models import User


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


@pytest.mark.asyncio
async def test_get_me_success(client, regular_user, user_headers):
    response = await client.get("/users/me", headers=user_headers)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["email"] == regular_user.email
    assert response_json.get("hashed_password", None) is None


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    response = await client.get("/users/me")

    assert response.status_code == 401


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
