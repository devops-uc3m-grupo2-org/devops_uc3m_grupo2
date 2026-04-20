import uuid


def _auth_context(client):
    email = f"news_{uuid.uuid4()}@mail.com"
    password = "admin123"

    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "News",
            "last_name": "Tester",
            "organization": "QA",
        },
    )
    assert r.status_code == 200

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_news(client):
    response = client.get("/api/v1/news")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_fetch_news_requires_auth(client):
    response = client.post("/api/v1/news/fetch")
    assert response.status_code == 401


def test_fetch_news_authenticated(client):
    headers = _auth_context(client)
    response = client.post("/api/v1/news/fetch", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "new_items" in data
    assert isinstance(data["new_items"], int)
