import uuid


def _auth(client):
    email = f"cat_{uuid.uuid4()}@mail.com"
    password = "admin123"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": password,
        "first_name": "Cat", "last_name": "Tester",
        "organization": "QA", "role_ids": [1],
    })
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_categories_requires_auth(client):
    response = client.get("/api/v1/categories")
    assert response.status_code == 401


def test_create_category(client):
    headers = _auth(client)
    response = client.post("/api/v1/categories", headers=headers, json={
        "name": f"Cat_{uuid.uuid4()}", "source": "manual"
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "name" in data


def test_list_categories(client):
    headers = _auth(client)
    client.post("/api/v1/categories", headers=headers, json={"name": f"Cat_{uuid.uuid4()}", "source": "manual"})
    response = client.get("/api/v1/categories", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_category_by_id(client):
    headers = _auth(client)
    created = client.post("/api/v1/categories", headers=headers, json={
        "name": f"Cat_{uuid.uuid4()}", "source": "manual"
    }).json()
    response = client.get(f"/api/v1/categories/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_category_not_found(client):
    headers = _auth(client)
    response = client.get("/api/v1/categories/99999", headers=headers)
    assert response.status_code == 404


def test_update_category(client):
    headers = _auth(client)
    created = client.post("/api/v1/categories", headers=headers, json={
        "name": f"Cat_{uuid.uuid4()}", "source": "manual"
    }).json()
    new_name = f"Updated_{uuid.uuid4()}"
    response = client.put(f"/api/v1/categories/{created['id']}", headers=headers, json={"name": new_name})
    assert response.status_code == 200
    assert response.json()["name"] == new_name


def test_update_category_not_found(client):
    headers = _auth(client)
    response = client.put("/api/v1/categories/99999", headers=headers, json={"name": "X"})
    assert response.status_code == 404


def test_delete_category(client):
    headers = _auth(client)
    created = client.post("/api/v1/categories", headers=headers, json={
        "name": f"Cat_{uuid.uuid4()}", "source": "manual"
    }).json()
    response = client.delete(f"/api/v1/categories/{created['id']}", headers=headers)
    assert response.status_code == 204
    get_resp = client.get(f"/api/v1/categories/{created['id']}", headers=headers)
    assert get_resp.status_code == 404


def test_delete_category_not_found(client):
    headers = _auth(client)
    response = client.delete("/api/v1/categories/99999", headers=headers)
    assert response.status_code == 404
