import uuid


def _auth(client):
    email = f"usr_{uuid.uuid4()}@mail.com"
    password = "admin123"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": password,
        "first_name": "User", "last_name": "Tester",
        "organization": "QA", "role_ids": [1],
    })
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _my_id(client, headers):
    return client.get("/api/v1/users", headers=headers).json()[-1]["id"]


def _make_alert(client, headers, user_id, name="test_alert"):
    return client.post(f"/api/v1/users/{user_id}/alerts", headers=headers, json={
        "name": name, "descriptors": ["kw"],
        "categories": [], "rss_channels_ids": [],
        "information_sources_ids": [], "cron_expression": "0 * * * *", "is_active": True,
    }).json()


# --- users ---

def test_get_user_by_id(client):
    headers = _auth(client)
    user_id = _my_id(client, headers)
    response = client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_get_user_not_found(client):
    headers = _auth(client)
    response = client.get("/api/v1/users/99999", headers=headers)
    assert response.status_code == 404


def test_update_user(client):
    headers = _auth(client)
    user_id = _my_id(client, headers)
    response = client.put(f"/api/v1/users/{user_id}", headers=headers, json={"first_name": "Changed"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Changed"


def test_update_user_duplicate_email(client):
    headers1 = _auth(client)
    headers2 = _auth(client)
    email1 = client.get("/api/v1/users", headers=headers1).json()[-2]["email"]
    user2_id = _my_id(client, headers2)
    response = client.put(f"/api/v1/users/{user2_id}", headers=headers2, json={"email": email1})
    assert response.status_code == 409


def test_create_user_direct_endpoint(client):
    headers = _auth(client)
    email = f"direct_{uuid.uuid4()}@mail.com"
    response = client.post("/api/v1/users", headers=headers, json={
        "email": email, "password": "pass1234",
        "first_name": "D", "last_name": "U", "organization": "QA", "role_ids": [1],
    })
    assert response.status_code == 201


def test_create_user_duplicate_email(client):
    headers = _auth(client)
    users = client.get("/api/v1/users", headers=headers).json()
    existing_email = users[0]["email"]
    response = client.post("/api/v1/users", headers=headers, json={
        "email": existing_email, "password": "pass1234",
        "first_name": "D", "last_name": "U", "organization": "QA", "role_ids": [],
    })
    assert response.status_code == 409


def test_delete_user(client):
    headers = _auth(client)
    email = f"del_{uuid.uuid4()}@mail.com"
    client.post("/api/v1/users", headers=headers, json={
        "email": email, "password": "pass1234",
        "first_name": "D", "last_name": "U", "organization": "QA", "role_ids": [],
    })
    new_id = client.get("/api/v1/users", headers=headers).json()[-1]["id"]
    response = client.delete(f"/api/v1/users/{new_id}", headers=headers)
    assert response.status_code == 204
    assert client.get(f"/api/v1/users/{new_id}", headers=headers).status_code == 404


# --- notifications ---

def test_list_notifications(client):
    headers = _auth(client)
    user_id = _my_id(client, headers)
    alert = _make_alert(client, headers, user_id, "notif_alert")
    response = client.get(f"/api/v1/users/{user_id}/alerts/{alert['id']}/notifications", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_notification(client):
    headers = _auth(client)
    user_id = _my_id(client, headers)
    alert = _make_alert(client, headers, user_id, "notif_create_alert")
    response = client.post(
        f"/api/v1/users/{user_id}/alerts/{alert['id']}/notifications",
        headers=headers,
        json={"timestamp": "2024-01-01T00:00:00", "metrics": []},
    )
    assert response.status_code == 201
    assert "id" in response.json()


def test_get_notification_by_id(client):
    headers = _auth(client)
    user_id = _my_id(client, headers)
    alert = _make_alert(client, headers, user_id, "notif_get_alert")
    notif = client.post(
        f"/api/v1/users/{user_id}/alerts/{alert['id']}/notifications",
        headers=headers,
        json={"timestamp": "2024-01-01T00:00:00", "metrics": []},
    ).json()
    response = client.get(
        f"/api/v1/users/{user_id}/alerts/{alert['id']}/notifications/{notif['id']}",
        headers=headers,
    )
    assert response.status_code == 200


def test_get_notification_not_found(client):
    headers = _auth(client)
    user_id = _my_id(client, headers)
    alert = _make_alert(client, headers, user_id, "notif_nf_alert")
    response = client.get(
        f"/api/v1/users/{user_id}/alerts/{alert['id']}/notifications/99999",
        headers=headers,
    )
    assert response.status_code == 404


def test_update_notification(client):
    headers = _auth(client)
    user_id = _my_id(client, headers)
    alert = _make_alert(client, headers, user_id, "notif_upd_alert")
    notif = client.post(
        f"/api/v1/users/{user_id}/alerts/{alert['id']}/notifications",
        headers=headers,
        json={"timestamp": "2024-01-01T00:00:00", "metrics": []},
    ).json()
    response = client.put(
        f"/api/v1/users/{user_id}/alerts/{alert['id']}/notifications/{notif['id']}",
        headers=headers,
        json={"timestamp": "2025-06-01T12:00:00"},
    )
    assert response.status_code == 200


def test_delete_notification(client):
    headers = _auth(client)
    user_id = _my_id(client, headers)
    alert = _make_alert(client, headers, user_id, "notif_del_alert")
    notif = client.post(
        f"/api/v1/users/{user_id}/alerts/{alert['id']}/notifications",
        headers=headers,
        json={"timestamp": "2024-01-01T00:00:00", "metrics": []},
    ).json()
    response = client.delete(
        f"/api/v1/users/{user_id}/alerts/{alert['id']}/notifications/{notif['id']}",
        headers=headers,
    )
    assert response.status_code == 204
