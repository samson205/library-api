import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.shelves.models import Shelf


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "image_data", [("image.jpg", b"fake-image-bytes-content", "image/jpeg"), None]
)
async def test_create_shelf_success(client, user_headers, image_data, mock_media_root):
    shelf_data = {"title": "shelf", "is_private": False}
    if image_data:
        response = await client.post(
            "/shelves/",
            data=shelf_data,
            files={"image": image_data},
            headers=user_headers,
        )
    else:
        response = await client.post("/shelves/", data=shelf_data, headers=user_headers)

    assert response.status_code == 201
    response_json = response.json()
    assert response_json.get("title") == shelf_data["title"]
    assert response_json.get("books_count") == 0
    if image_data:
        assert response_json.get("image_url") is not None

        files_in_storage = [f for f in mock_media_root.glob("**/*") if f.is_file()]
        assert len(files_in_storage) == 1

        saved_file_book = files_in_storage[0]
        assert saved_file_book.is_file()
        assert saved_file_book.stat().st_size > 0
    else:
        assert response_json.get("image_url") is None


@pytest.mark.asyncio
async def test_create_shelf_unauthorized(client):
    shelf_data = {"title": "shlef", "is_private": False}
    response = await client.post("/shelves/", data=shelf_data)

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("use_user,expected_count", [(False, 2), (True, 1)])
async def test_get_shelves_success(
    client,
    db_session,
    use_user,
    regular_user,
    user_with_img,
    user_with_img_headers,
    expected_count,
):
    shelf1 = Shelf(title="shelf1", is_private=False, user_id=regular_user.id)
    shelf2 = Shelf(title="shelf2", is_private=True, user_id=regular_user.id)
    shelf3 = Shelf(title="shelf3", is_private=False, user_id=user_with_img.id)
    db_session.add_all([shelf1, shelf2, shelf3])
    await db_session.flush()

    params = []
    if use_user:
        params.append(("user_id", regular_user.id))
    response = await client.get(
        "/shelves/", params=params, headers=user_with_img_headers
    )

    assert response.status_code == 200
    response_json = response.json()
    shelves = response_json.get("items")
    assert response_json.get("total") == expected_count
    assert isinstance(shelves, list)
    assert len(shelves) == expected_count


@pytest.mark.asyncio
async def test_get_zero_shelves(client):
    response = await client.get("/shelves/")

    assert response.status_code == 200
    assert response.json().get("total") == 0


@pytest.mark.asyncio
async def test_get_shelves_incorrect_page_size(client):
    params = [("page_size", 100)]
    response = await client.get("/shelves/", params=params)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_shelf_by_id_success(client, existing_shelf):
    response = await client.get(f"/shelves/{existing_shelf.id}")

    assert response.status_code == 200
    assert response.json().get("title") == existing_shelf.title


@pytest.mark.asyncio
async def test_get_private_shelf_by_owner(client, private_shelf, user_headers):
    response = await client.get(f"/shelves/{private_shelf.id}", headers=user_headers)

    assert response.status_code == 200
    assert response.json().get("title") == private_shelf.title


@pytest.mark.asyncio
async def test_get_private_shelf_by_another_user(
    client, private_shelf, user_with_img_headers
):
    response = await client.get(
        f"/shelves/{private_shelf.id}", headers=user_with_img_headers
    )

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_get_shelf_not_found(client):
    response = await client.get(f"/shelves/101")

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_update_shelf_success(client, existing_shelf, user_headers):
    upd_data = {"title": "upd_title"}
    response = await client.patch(
        f"/shelves/{existing_shelf.id}", json=upd_data, headers=user_headers
    )

    assert response.status_code == 200
    assert response.json().get("title") == upd_data["title"]


@pytest.mark.asyncio
async def test_update_shelf_by_anonymous_unauthorized(client, existing_shelf):
    upd_data = {"title": "upd_title"}
    response = await client.patch(f"/shelves/{existing_shelf.id}", json=upd_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_public_shelf_by_another_user_forbidden(
    client, existing_shelf, user_with_img_headers
):
    upd_data = {"title": "upd_title"}
    response = await client.patch(
        f"/shelves/{existing_shelf.id}", json=upd_data, headers=user_with_img_headers
    )

    assert response.status_code == 403
    assert response.json().get("detail") == "You don't have access"


@pytest.mark.asyncio
async def test_update_private_shelf_by_another_user_not_found(
    client, private_shelf, user_with_img_headers
):
    upd_data = {"title": "upd_title"}
    response = await client.patch(
        f"/shelves/{private_shelf.id}", json=upd_data, headers=user_with_img_headers
    )

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_update_shelf_not_found(client, user_headers):
    upd_data = {"title": "upd_title"}
    response = await client.patch(f"/shelves/101", json=upd_data, headers=user_headers)

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_delete_shelf_success(client, db_session, existing_shelf, user_headers):
    response = await client.delete(
        f"/shelves/{existing_shelf.id}", headers=user_headers
    )

    assert response.status_code == 204

    result = await db_session.scalars(
        select(Shelf).where(Shelf.id == existing_shelf.id)
    )
    shelf = result.first()
    assert shelf is None


@pytest.mark.asyncio
async def test_delete_shelf_by_another_user_forbidden(
    client, existing_shelf, user_with_img_headers
):
    response = await client.delete(
        f"/shelves/{existing_shelf.id}", headers=user_with_img_headers
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_shelf_not_found(client, user_headers):
    response = await client.delete("/shelves/101", headers=user_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_shelf_image_success(
    client, db_session, existing_shelf, user_headers, mock_media_root
):
    assert existing_shelf.image_url is None

    image_data = {"image": ("image.jpg", b"fake-image-bytes-content", "image/jpeg")}
    response = await client.put(
        f"/shelves/{existing_shelf.id}/image", files=image_data, headers=user_headers
    )

    assert response.status_code == 200

    await db_session.refresh(existing_shelf)
    assert existing_shelf.image_url is not None

    files_in_media = [f for f in mock_media_root.glob("**/*") if f.is_file()]
    assert len(files_in_media) == 1
    saved_file = files_in_media[0]
    assert saved_file.is_file()
    assert saved_file.stat().st_size > 0


@pytest.mark.asyncio
async def test_update_shelf_image_not_found(client, user_headers):
    image_data = {"image": ("image.jpg", b"fake-image-bytes-content", "image/jpeg")}
    response = await client.put(
        "/shelves/101/image", files=image_data, headers=user_headers
    )

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_update_shelf_image_by_another_user(
    client, existing_shelf, user_with_img_headers
):
    image_data = {"image": ("image.jpg", b"fake-image-bytes-content", "image/jpeg")}
    response = await client.put(
        f"/shelves/{existing_shelf.id}/image",
        files=image_data,
        headers=user_with_img_headers,
    )

    assert response.status_code == 403
    assert (
        response.json().get("detail")
        == "You can change the image of only your own shelf"
    )


@pytest.mark.asyncio
async def test_update_shelf_image_too_big(client, existing_shelf, user_headers):
    image_data = {
        "image": ("image.jpg", b"0" * (settings.MAX_IMAGE_SIZE + 100), "image/jpeg")
    }
    response = await client.put(
        f"/shelves/{existing_shelf.id}/image", files=image_data, headers=user_headers
    )

    assert response.status_code == 400
    assert response.json().get("detail") == "File is too large"


@pytest.mark.asyncio
async def test_update_shelf_image_incorrect_type(client, existing_shelf, user_headers):
    image_data = {"image": ("image.gif", b"fake-image-bytes-content", "image/gif")}
    response = await client.put(
        f"/shelves/{existing_shelf.id}/image", files=image_data, headers=user_headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_shelf_image_success(
    client, shelf_with_img, user_headers, mock_media_root
):
    fake_image_path = mock_media_root / shelf_with_img.image_url
    fake_image_path.parent.mkdir(parents=True, exist_ok=True)
    fake_image_path.write_bytes(b"fake-image-bytes-content")
    assert fake_image_path.exists()

    response = await client.delete(
        f"/shelves/{shelf_with_img.id}/image", headers=user_headers
    )

    assert response.status_code == 204

    files_in_media = [f for f in mock_media_root.glob("**/*") if f.is_file()]
    assert len(files_in_media) == 0


@pytest.mark.asyncio
async def test_delete_shelf_image_not_found(client, user_headers):
    response = await client.delete("/shelves/101/image", headers=user_headers)

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_delete_shelf_image_by_another_user(
    client, existing_shelf, user_with_img_headers
):
    response = await client.delete(
        f"/shelves/{existing_shelf.id}/image", headers=user_with_img_headers
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_book_to_shelf_success(
    client, db_session, existing_shelf, existing_book, user_headers
):
    response = await client.post(
        f"/shelves/{existing_shelf.id}/books/{existing_book.id}", headers=user_headers
    )

    assert response.status_code == 201

    result = await db_session.scalars(
        select(Shelf)
        .options(selectinload(Shelf.books))
        .where(Shelf.id == existing_shelf.id)
    )
    shelf = result.first()
    assert shelf is not None
    assert len(shelf.books) == 1
    assert shelf.books[0].title == existing_book.title


@pytest.mark.asyncio
async def test_add_book_to_shelf_by_another_user(
    client, existing_shelf, existing_book, user_with_img_headers
):
    response = await client.post(
        f"/shelves/{existing_shelf.id}/books/{existing_book.id}",
        headers=user_with_img_headers,
    )

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_add_book_to_shelf_not_found(client, existing_book, user_headers):
    response = await client.post(
        f"/shelves/101/books/{existing_book.id}", headers=user_headers
    )

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_add_book_to_shelf_book_not_found(client, existing_shelf, user_headers):
    response = await client.post(
        f"/shelves/{existing_shelf.id}/books/101", headers=user_headers
    )

    assert response.status_code == 404
    assert response.json().get("detail") == "Book not found or inactive"


@pytest.mark.asyncio
async def test_delete_book_from_shelf_success(
    client, db_session, shelf_with_book, existing_book, user_headers
):
    response = await client.delete(
        f"/shelves/{shelf_with_book.id}/books/{existing_book.id}", headers=user_headers
    )

    assert response.status_code == 200

    result = await db_session.scalars(
        select(Shelf)
        .options(selectinload(Shelf.books))
        .where(Shelf.id == shelf_with_book.id)
    )
    shelf = result.first()
    assert shelf is not None
    assert len(shelf.books) == 0


@pytest.mark.asyncio
async def test_delete_book_from_shelf_by_another_user(
    client, existing_shelf, existing_book, user_with_img_headers
):
    response = await client.delete(
        f"/shelves/{existing_shelf.id}/books/{existing_book.id}",
        headers=user_with_img_headers,
    )

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_delete_book_from_shelf_not_found(client, existing_book, user_headers):
    response = await client.delete(
        f"/shelves/101/books/{existing_book.id}", headers=user_headers
    )

    assert response.status_code == 404
    assert response.json().get("detail") == "Shelf not found or you don't have access"


@pytest.mark.asyncio
async def test_delete_book_from_shelf_book_not_found(
    client, existing_shelf, user_headers
):
    response = await client.delete(
        f"/shelves/{existing_shelf.id}/books/101", headers=user_headers
    )

    assert response.status_code == 404
    assert response.json().get("detail") == "Book not found or inactive"
