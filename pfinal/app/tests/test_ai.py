import uuid


def _auth_context(client):
    email = f"ai_{uuid.uuid4()}@mail.com"
    password = "admin123"

    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "AI",
            "last_name": "Tester",
            "organization": "QA",
        },
    )
    assert r.status_code == 200

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_suggestions_known_keyword(client):
    headers = _auth_context(client)
    response = client.get("/api/v1/suggestions?keyword=economía", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["keyword"] == "economía"
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    assert "economía" in data["suggestions"]


def test_suggestions_unknown_keyword(client):
    headers = _auth_context(client)
    response = client.get("/api/v1/suggestions?keyword=xyzdesconocido", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["keyword"] == "xyzdesconocido"
    assert isinstance(data["suggestions"], list)
    assert any("xyzdesconocido" in s for s in data["suggestions"])


def test_suggestions_requires_auth(client):
    response = client.get("/api/v1/suggestions?keyword=economía")
    assert response.status_code == 401
