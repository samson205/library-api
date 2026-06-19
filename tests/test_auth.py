import pytest


@pytest.mark.asyncio
async def test_create_user_success(client):
    user_data = {"email": "test@test.com", "password": "test_test"}
    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 201
    response_json = response.json()
    assert response_json.get("access_token") is not None
    assert response_json.get("refresh_token") is not None
    assert response_json["user"]["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client, regular_user):
    user_data = {"email": regular_user.email, "password": "test_test"}
    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_create_user_with_incorrect_email(client):
    user_data = {"email": "abcbcbc", "password": "test_test"}
    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_short_password(client):
    user_data = {"email": "test@test.com", "password": "test"}
    response = await client.post("/auth/register", json=user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, regular_user):
    user_data = {"username": regular_user.email, "password": "reader123"}
    response = await client.post("/auth/login", data=user_data)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json.get("access_token") is not None
    assert response_json.get("refresh_token") is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username,password",
    [("wrong_email@test.com", "reader123"), ("reader@test.com", "wrong_password")],
)
async def test_login_credentials_fail(client, regular_user, username, password):
    user_data = {"username": username, "password": password}
    response = await client.post("/auth/login", data=user_data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_access_token_success(client, refresh_token):
    data = {"refresh_token": refresh_token}
    response = await client.post("/auth/access-token", json=data)

    assert response.status_code == 200
    assert response.json().get("access_token") is not None


@pytest.mark.asyncio
async def test_access_token_incorrect(client):
    data = {"refresh_token": "refresh_token"}
    response = await client.post("/auth/access-token", json=data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate refresh token"


@pytest.mark.asyncio
async def test_refresh_token_success(client, refresh_token):
    data = {"refresh_token": refresh_token}
    response = await client.post("/auth/refresh-token", json=data)

    assert response.status_code == 200
    assert response.json().get("refresh_token") is not None


@pytest.mark.asyncio
async def test_refresh_token_incorrect(client):
    data = {"refresh_token": "refresh_token"}
    response = await client.post("/auth/refresh-token", json=data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate refresh token"
