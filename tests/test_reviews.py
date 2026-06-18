import pytest
from sqlalchemy import select

from app.reviews.models import Review


@pytest.mark.asyncio
async def test_create_review_success(client, db_session, existing_book, user_headers):
    review_data = {"book_id": existing_book.id, "comment": "good", "grade": 5}
    response = await client.post("/reviews/", json=review_data, headers=user_headers)

    assert response.status_code == 201
    response_json = response.json()
    assert response_json.get("book_id") == existing_book.id
    
    await db_session.refresh(existing_book)
    assert existing_book.rating == response_json.get("grade")


@pytest.mark.asyncio
async def test_create_review_unauthorized(client, existing_book):
    review_data = {"book_id": existing_book.id, "comment": "good", "grade": 5}
    response = await client.post("/reviews/", json=review_data)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_review_book_not_found(client, user_headers):
    review_data = {"book_id": 101, "comment": "good", "grade": 5}
    response = await client.post("/reviews/", json=review_data, headers=user_headers)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found or inactive"
    

@pytest.mark.asyncio
async def test_create_review_incorrect_grade(client, existing_book, user_headers):
    review_data = {"book_id": existing_book.id, "comment": "good", "grade": 6}
    response = await client.post("/reviews/", json=review_data, headers=user_headers)
    
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "use_user,use_book,expected_count",
    [(False, False, 2), (False, True, 1), (True, False, 1), (True, True, 1)],
)
async def test_get_reviews_success(
    client, db_session, existing_book, another_book, regular_user, user_with_img, use_user, use_book, expected_count
):
    review1 = Review(comment="good", grade=4, user_id=regular_user.id, book_id=existing_book.id)
    review2 = Review(comment="great", grade=5, user_id=user_with_img.id, book_id=another_book.id)
    db_session.add_all([review1, review2])
    await db_session.flush()

    params = []
    if use_user:
        params.append(("user_id", regular_user.id))
    if use_book:
        params.append(("book_id", existing_book.id))
    response = await client.get("/reviews/", params=params)

    assert response.status_code == 200
    response_json = response.json()
    reviews = response_json.get("items")
    assert response_json.get("total") == expected_count
    assert isinstance(reviews, list)
    assert len(reviews) == expected_count


@pytest.mark.asyncio
async def test_get_zero_reviews(client):
    response = await client.get("/reviews/")

    assert response.status_code == 200
    response_json = response.json()
    reviews = response_json.get("items")
    assert response_json.get("total") == 0
    assert isinstance(reviews, list)
    assert len(reviews) == 0


@pytest.mark.asyncio
async def test_delete_review_success(client, db_session, existing_review, user_headers):
    response = await client.delete(f"/reviews/{existing_review.id}", headers=user_headers)

    assert response.status_code == 204

    result = await db_session.scalars(
        select(Review).where(Review.id == existing_review.id)
    )
    assert result.first() is None


@pytest.mark.asyncio
async def test_delete_review_not_found(client, user_headers):
    response = await client.delete("/reviews/101", headers=user_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"


@pytest.mark.asyncio
async def test_delete_review_by_another_user_forbidden(client, existing_review, user_with_img_headers):
    response = await client.delete(f"/reviews/{existing_review.id}", headers=user_with_img_headers)

    assert response.status_code == 403
