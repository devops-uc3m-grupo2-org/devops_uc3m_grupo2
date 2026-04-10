import uuid

def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@newsradar.com",
            "password": "admin123"
        }
    )

    assert response.status_code == 200
    body = response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_fail(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@newsradar.com",
            "password": "wrong"
        }
    )

    assert response.status_code == 401



def test_register_user(client):
    email = f"test_{uuid.uuid4()}@mail.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "123456",
            "first_name": "Test",
            "last_name": "User",
            "organization": "QA"
        }
    )

    assert response.status_code == 200
    assert response.json()["email"] == email