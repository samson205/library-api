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
