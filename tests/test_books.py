import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.books.models import Book


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "image_data", [("image.jpg", b"fake-image-bytes-content", "image/jpeg"), None]
)
async def test_create_book_by_admin_success(
    client,
    db_session,
    existing_genre,
    existing_author,
    admin_headers,
    mock_storage_root,
    mock_media_root,
    image_data,
):
    book_data = {
        "title": "book",
        "genre_id": existing_genre.id,
        "author_ids": [existing_author.id],
    }
    files = {"book_file": ("book.pdf", b"fake-book-bytes-content", "application/pdf")}
    if image_data:
        files["image"] = image_data
    response = await client.post(
        "/books/", data=book_data, files=files, headers=admin_headers
    )

    assert response.status_code == 201
    response_json = response.json()
    assert response_json.get("title") == book_data["title"]
    assert response_json.get("authors")[0]["first_name"] == existing_author.first_name
    assert response_json.get("genre")["name"] == existing_genre.name

    result = await db_session.scalars(
        select(Book)
        .options(
            selectinload(Book.authors),
            selectinload(Book.genre),
            selectinload(Book.files),
        )
        .where(Book.id == response_json["id"])
    )
    book = result.first()
    assert book is not None
    assert book.authors is not None
    assert book.files is not None
    assert book.genre == existing_genre

    files_in_storage = [f for f in mock_storage_root.glob("**/*") if f.is_file()]
    assert len(files_in_storage) == 1

    saved_file_book = files_in_storage[0]
    assert saved_file_book.is_file()
    assert saved_file_book.stat().st_size > 0

    if image_data:
        assert book.image_url is not None

        files_in_image = [f for f in mock_media_root.glob("**/*") if f.is_file()]
        assert len(files_in_image) == 1

        saved_file_image = files_in_image[0]
        assert saved_file_image.is_file()
        assert saved_file_image.stat().st_size > 0
    else:
        assert book.image_url is None


@pytest.mark.asyncio
async def test_create_book_by_regular_user_forbidden(
    client, existing_genre, existing_author, user_headers
):
    book_data = {
        "title": "book",
        "genre_id": existing_genre.id,
        "author_ids": [existing_author.id],
    }
    files = {"book_file": ("book.pdf", b"fake-book-bytes-content", "application/pdf")}
    response = await client.post(
        "/books/", data=book_data, files=files, headers=user_headers
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_book_by_anonymous_unauthorized(
    client, existing_genre, existing_author
):
    book_data = {
        "title": "book",
        "genre_id": existing_genre.id,
        "author_ids": [existing_author.id],
    }
    files = {"book_file": ("book.pdf", b"fake-book-bytes-content", "application/pdf")}
    response = await client.post("/books/", data=book_data, files=files)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_book_incorrect_book_type(
    client, existing_genre, existing_author, admin_headers
):
    book_data = {
        "title": "book",
        "genre_id": existing_genre.id,
        "author_ids": [existing_author.id],
    }
    files = {"book_file": ("book.gif", b"fake-book-bytes-content", "image/gif")}
    response = await client.post(
        "/books/", data=book_data, files=files, headers=admin_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only .epub, .fb2, .pdf files are allowed"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "image_data",
    [("image.jpg", b"0" * (settings.MAX_IMAGE_SIZE + 100), "image/jpeg"), None],
)
async def test_create_book_file_too_big(
    client, existing_genre, existing_author, admin_headers, image_data
):
    book_data = {
        "title": "book",
        "genre_id": existing_genre.id,
        "author_ids": [existing_author.id],
    }
    if image_data:
        files = files = {
            "book_file": ("book.pdf", b"fake-book-bytes-content", "application/pdf"),
            "image": (
                "image.jpg",
                b"0" * (settings.MAX_IMAGE_SIZE + 100),
                "image/jpeg",
            ),
        }
    else:
        files = {
            "book_file": (
                "book.pdf",
                b"0" * (settings.MAX_BOOK_SIZE + 100),
                "application/pdf",
            )
        }

    response = await client.post(
        "/books/", data=book_data, files=files, headers=admin_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File is too large"


@pytest.mark.asyncio
async def test_add_book_file_by_admin_success(client, existing_book, admin_headers, mock_storage_root):
    file_data = {"file": ("book.pdf", b"fake-book-bytes-content", "application/pdf")}
    response = await client.post(f"/books/{existing_book.id}/files", files=file_data, headers=admin_headers)

    assert response.status_code == 201
    response_json = response.json()
    assert len(response_json.get("files")) == 1

    files_in_storage = [f for f in mock_storage_root.glob("**/*") if f.is_file()]
    saved_file = files_in_storage[0]
    assert len(files_in_storage) == 1
    assert saved_file is not None
    assert saved_file.is_file()
    assert saved_file.stat().st_size > 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "use_headers, expected_status",
    [(True, 403), (False, 401)]
)
async def test_add_book_file_forbidden_or_unauthorized(client, existing_book, user_headers, use_headers, expected_status):
    file_data = {"file": ("book.pdf", b"fake-book-bytes-content", "application/pdf")}
    if use_headers:
        response = await client.post(f"/books/{existing_book.id}/files", files=file_data, headers=user_headers)
    else:
        response = await client.post(f"/books/{existing_book.id}/files", files=file_data)

    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_add_book_file_too_big(client, existing_book, admin_headers):
    file_data = {"file": ("book.pdf", b"0" * (settings.MAX_BOOK_SIZE + 100), "application/pdf")}
    response = await client.post(f"/books/{existing_book.id}/files", files=file_data, headers=admin_headers)

    assert response.status_code == 400
    assert response.json().get("detail") == "File is too large"


@pytest.mark.asyncio
async def test_add_book_file_incorrect_type(client, existing_book, admin_headers):
    file_data = {"file": ("book.pdf", b"0" * (settings.MAX_BOOK_SIZE + 100), "application/pdf")}
    response = await client.post(f"/books/{existing_book.id}/files", files=file_data, headers=admin_headers)

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "use_author,use_genre,expected_count",
    [(False, False, 3), (False, True, 2), (True, False, 2), (True, True, 2)],
)
async def test_get_books_success(
    client,
    db_session,
    existing_genre,
    existing_author,
    another_book,
    use_author,
    use_genre,
    expected_count,
):
    book1 = Book(title="Обломов", genre_id=existing_genre.id, authors=[existing_author])
    book2 = Book(
        title="Война и мир", genre_id=existing_genre.id, authors=[existing_author]
    )
    db_session.add_all([book1, book2])
    await db_session.flush()

    params = []
    if use_author:
        params.append(("author_ids", existing_author.id))
    if use_genre:
        params.append(("genre_id", existing_genre.id))
    response = await client.get("/books/", params=params)

    assert response.status_code == 200
    response_json = response.json()
    books = response_json.get("items")
    assert response_json.get("page") == 1
    assert response_json.get("total") == expected_count
    assert isinstance(books, list)
    assert len(books) == expected_count


@pytest.mark.asyncio
async def test_get_books_excluded_inactive(
    client, db_session, existing_genre, existing_author
):
    book1 = Book(title="Обломов", genre_id=existing_genre.id, authors=[existing_author])
    book2 = Book(
        title="Война и мир",
        genre_id=existing_genre.id,
        authors=[existing_author],
        is_active=False,
    )
    db_session.add_all([book1, book2])
    await db_session.flush()

    response = await client.get("/books/")

    assert response.status_code == 200
    response_json = response.json()
    books = response_json.get("items")
    assert response_json.get("total") == 1
    assert isinstance(books, list)
    assert len(books) == 1


@pytest.mark.asyncio
async def test_get_zero_books(client):
    response = await client.get("/books/")

    assert response.status_code == 200
    response_json = response.json()
    books = response_json.get("items")
    assert response_json.get("total") == 0
    assert isinstance(books, list)
    assert len(books) == 0


@pytest.mark.asyncio
async def test_get_books_incorrect_page_size(client):
    params = {"page_size": 100}
    response = await client.get("/books/", params=params)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_book_by_id_success(client, existing_book):
    response = await client.get(f"/books/{existing_book.id}")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["title"] == existing_book.title
    assert response_json["genre"]["id"] == existing_book.genre_id


@pytest.mark.asyncio
@pytest.mark.parametrize("is_exist", [False, True])
async def test_get_book_by_id_not_found(
    client, db_session, existing_author, existing_genre, is_exist
):
    inactive_book = Book(
        title="Обломов",
        genre_id=existing_genre.id,
        authors=[existing_author],
        is_active=False,
    )
    db_session.add(inactive_book)
    await db_session.flush()
    await db_session.refresh(inactive_book)

    url = f"/books/{inactive_book.id}" if is_exist else "/books/101"
    response = await client.get(url)

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found or inactive"


@pytest.mark.asyncio
async def test_update_book_by_admin_success(
    client, db_session, existing_book, admin_headers
):
    upd_data = {"title": "new_title"}
    response = await client.patch(
        f"/books/{existing_book.id}", json=upd_data, headers=admin_headers
    )

    assert response.status_code == 200
    await db_session.refresh(existing_book)
    assert existing_book.title == upd_data["title"]
    assert response.json()["title"] == upd_data["title"]


@pytest.mark.asyncio
@pytest.mark.parametrize("use_headers,expected_status", [(True, 403), (False, 401)])
async def test_update_book_forbidden_or_unauthorized(
    client, existing_book, user_headers, use_headers, expected_status
):
    upd_data = {"title": "new_title"}
    if use_headers:
        response = await client.patch(
            f"/books/{existing_book.id}", json=upd_data, headers=user_headers
        )
    else:
        response = await client.patch(f"/books/{existing_book.id}", json=upd_data)

    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_update_book_not_found(client, admin_headers):
    upd_data = {"title": "new_title"}
    response = await client.patch("/books/101", json=upd_data, headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found or inactive"


@pytest.mark.asyncio
async def test_soft_delete_book_by_admin_success(
    client, db_session, existing_book, admin_headers
):
    response = await client.delete(f"/books/{existing_book.id}", headers=admin_headers)

    assert response.status_code == 204
    await db_session.refresh(existing_book)
    assert existing_book.is_active == False


@pytest.mark.asyncio
@pytest.mark.parametrize("use_headers,expected_status", [(True, 403), (False, 401)])
async def test_soft_delete_book_forbidden_or_unauthorized(
    client, existing_book, user_headers, use_headers, expected_status
):
    if use_headers:
        response = await client.delete(
            f"/books/{existing_book.id}", headers=user_headers
        )
    else:
        response = await client.delete(f"/books/{existing_book.id}")

    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_soft_delete_book_not_found(client, admin_headers):
    response = await client.delete("/books/101", headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found or inactive"


@pytest.mark.asyncio
async def test_update_book_image_by_admin_success(
    client, db_session, existing_book, admin_headers, mock_media_root
):
    file_data = {"image": ("image.jpg", b"fake-image-bytes-content", "image/jpeg")}
    response = await client.put(
        f"/books/{existing_book.id}/image", files=file_data, headers=admin_headers
    )

    assert response.status_code == 200

    await db_session.refresh(existing_book)
    assert existing_book.image_url is not None

    files_in_media = [f for f in mock_media_root.glob("**/*") if f.is_file()]
    assert len(files_in_media) == 1

    saved_file = files_in_media[0]
    assert saved_file.is_file()
    assert saved_file.stat().st_size > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("use_headers,expected_status", [(True, 403), (False, 401)])
async def test_update_book_image_forbidden_or_unauthorized(
    client, existing_book, user_headers, use_headers, expected_status
):
    file_data = {"image": ("image.jpg", b"fake-image-bytes-content", "image/jpeg")}
    if use_headers:
        response = await client.put(
            f"/books/{existing_book.id}/image", files=file_data, headers=user_headers
        )
    else:
        response = await client.put(f"/books/{existing_book.id}/image", files=file_data)

    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_update_book_image_incorrect_type(client, existing_book, admin_headers):
    file_data = {"image": ("image.gif", b"fake-image-bytes-content", "image/gif")}
    response = await client.put(
        f"/books/{existing_book.id}/image", files=file_data, headers=admin_headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_book_image_too_big(client, existing_book, admin_headers):
    file_data = {
        "image": ("image.jpg", b"0" * (settings.MAX_IMAGE_SIZE + 100), "image/jpeg")
    }
    response = await client.put(
        f"/books/{existing_book.id}/image", files=file_data, headers=admin_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File is too large"


@pytest.mark.asyncio
async def test_delete_book_image_by_admin_success(
    client, db_session, existing_book, admin_headers, mock_media_root
):
    fake_image_path = mock_media_root / existing_book.image_url
    fake_image_path.parent.mkdir(parents=True, exist_ok=True)
    fake_image_path.write_bytes(b"fake-image-bytes-content")
    assert fake_image_path.exists() == True

    response = await client.delete(
        f"/books/{existing_book.id}/image", headers=admin_headers
    )

    assert response.status_code == 204
    assert fake_image_path.exists() == False

    await db_session.refresh(existing_book)
    assert existing_book.image_url is None


@pytest.mark.asyncio
@pytest.mark.parametrize("use_headers,expected_status", [(True, 403), (False, 401)])
async def test_delete_book_image_forbidden_or_unauthorized(
    client, existing_book, user_headers, use_headers, expected_status
):
    if use_headers:
        response = await client.delete(
            f"/books/{existing_book.id}/image", headers=user_headers
        )
    else:
        response = await client.delete(f"/books/{existing_book.id}/image")

    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_delete_book_image_not_found(client, admin_headers):
    response = await client.delete(
        f"/books/101/image", headers=admin_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found or inactive"


@pytest.mark.asyncio
async def test_delete_book_image_missing_on_disk(
    client, db_session, existing_book, admin_headers, mock_media_root
):
    assert existing_book.image_url is not None
    assert (mock_media_root / existing_book.image_url).exists() is False

    response = await client.delete(
        f"/books/{existing_book.id}/image", headers=admin_headers
    )

    assert response.status_code == 204

    await db_session.refresh(existing_book)
    assert existing_book.image_url is None


@pytest.mark.asyncio
async def test_read_book_by_regular_user_success(client, book_with_file, user_headers, mock_storage_root):
    fake_content = b"fake-file-bytes-content"
    fake_file_path = mock_storage_root / book_with_file.files[0].file_path
    fake_file_path.parent.mkdir(parents=True, exist_ok=True)
    fake_file_path.write_bytes(fake_content)
    params = {"file_type": "pdf"}
    response = await client.get(f"/books/{book_with_file.id}/read", params=params, headers=user_headers)

    assert response.status_code == 200
    assert response.content == fake_content 
    assert response.headers.get("content-type") == "application/pdf"


@pytest.mark.asyncio
async def test_read_book_by_anonymous_unauthorized(client, book_with_file):
    params = {"file_type": "pdf"}
    response = await client.get(f"/books/{book_with_file.id}/read", params=params)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_read_book_file_missing_on_disk(client, book_with_file, user_headers, mock_storage_root):
    fake_file_path = mock_storage_root / book_with_file.files[0].file_path
    assert fake_file_path.exists() == False

    params = {"file_type": "pdf"}
    response = await client.get(f"/books/{book_with_file.id}/read", params=params, headers=user_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Book file not found"
