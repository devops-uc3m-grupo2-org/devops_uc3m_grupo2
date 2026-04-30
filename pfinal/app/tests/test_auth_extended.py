import uuid


def _register_admin(client):
    email = f"auth_{uuid.uuid4()}@mail.com"
    password = "admin123"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": password,
        "first_name": "Auth", "last_name": "Tester",
        "organization": "QA", "role_ids": [1],
    })
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return email, {"Authorization": f"Bearer {token}"}


def test_verify_invalid_token(client):
    response = client.get("/api/v1/auth/verify?token=tokeninvalido")
    assert response.status_code == 400


def test_verify_wrong_purpose(client):
    email, headers = _register_admin(client)
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "admin123"})
    token = login.json()["access_token"]
    response = client.get(f"/api/v1/auth/verify?token={token}")
    assert response.status_code == 400


def test_forgot_password_unknown_email(client):
    response = client.post("/api/v1/auth/forgot-password", json={"email": "noexiste@mail.com"})
    assert response.status_code == 200
    assert "message" in response.json()


def test_forgot_password_known_email(client):
    email, _ = _register_admin(client)
    response = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    assert "message" in response.json()


def test_reset_password_invalid_token(client):
    response = client.post("/api/v1/auth/reset-password", json={
        "token": "tokeninvalido",
        "new_password": "nuevapass123"
    })
    assert response.status_code == 400


def test_reset_password_short_password(client):
    email, _ = _register_admin(client)
    response = client.post("/api/v1/auth/reset-password", json={
        "token": "tokeninvalido",
        "new_password": "abc"
    })
    assert response.status_code in [400, 422]


def test_register_duplicate_email(client):
    email = f"dup_{uuid.uuid4()}@mail.com"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "pass123",
        "first_name": "A", "last_name": "B", "organization": "QA",
    })
    response = client.post("/api/v1/auth/register", json={
        "email": email, "password": "pass123",
        "first_name": "A", "last_name": "B", "organization": "QA",
    })
    assert response.status_code == 409
