def _auth_headers(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@newsradar.com", "password": "admin123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_suggestions_known_keyword(client):
    headers = _auth_headers(client)
    response = client.get("/api/v1/suggestions?keyword=economía", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["keyword"] == "economía"
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0
    assert all(isinstance(s, str) for s in data["suggestions"])


def test_suggestions_unknown_keyword(client):
    headers = _auth_headers(client)
    response = client.get("/api/v1/suggestions?keyword=xyzdesconocido", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["keyword"] == "xyzdesconocido"
    assert isinstance(data["suggestions"], list)


def test_suggestions_requires_auth(client):
    response = client.get("/api/v1/suggestions?keyword=economía")
    assert response.status_code == 401
