import uuid


def _auth(client):
    email = f"role_{uuid.uuid4()}@mail.com"
    password = "admin123"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": password,
        "first_name": "Role", "last_name": "Tester",
        "organization": "QA", "role_ids": [1],
    })
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_roles_requires_auth(client):
    response = client.get("/api/v1/roles")
    assert response.status_code == 401


def test_list_roles(client):
    headers = _auth(client)
    response = client.get("/api/v1/roles", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # admin and user seeded in setup


def test_create_role(client):
    headers = _auth(client)
    name = f"role_{uuid.uuid4().hex[:8]}"
    response = client.post("/api/v1/roles", headers=headers, json={"name": name})
    assert response.status_code == 201
    assert response.json()["name"] == name


def test_get_role_by_id(client):
    headers = _auth(client)
    created = client.post("/api/v1/roles", headers=headers, json={"name": f"role_{uuid.uuid4().hex[:8]}"}).json()
    response = client.get(f"/api/v1/roles/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_role_not_found(client):
    headers = _auth(client)
    response = client.get("/api/v1/roles/99999", headers=headers)
    assert response.status_code == 404


def test_update_role(client):
    headers = _auth(client)
    created = client.post("/api/v1/roles", headers=headers, json={"name": f"role_{uuid.uuid4().hex[:8]}"}).json()
    new_name = f"updated_{uuid.uuid4().hex[:8]}"
    response = client.put(f"/api/v1/roles/{created['id']}", headers=headers, json={"name": new_name})
    assert response.status_code == 200
    assert response.json()["name"] == new_name


def test_update_role_not_found(client):
    headers = _auth(client)
    response = client.put("/api/v1/roles/99999", headers=headers, json={"name": "ghost"})
    assert response.status_code == 404


def test_delete_role_unassigned(client):
    headers = _auth(client)
    created = client.post("/api/v1/roles", headers=headers, json={"name": f"role_{uuid.uuid4().hex[:8]}"}).json()
    response = client.delete(f"/api/v1/roles/{created['id']}", headers=headers)
    assert response.status_code == 204


def test_delete_role_not_found(client):
    headers = _auth(client)
    response = client.delete("/api/v1/roles/99999", headers=headers)
    assert response.status_code == 404


def test_delete_assigned_role_returns_409(client):
    headers = _auth(client)
    # Role 1 (admin) is assigned to the user we just created
    response = client.delete("/api/v1/roles/1", headers=headers)
    assert response.status_code == 409
