import uuid


def _auth_context(client):
    email = f"stats_{uuid.uuid4()}@mail.com"
    password = "admin123"

    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Stats",
            "last_name": "Tester",
            "organization": "QA",
            "role_ids": [1],
        },
    )
    assert r.status_code == 201

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_stats_returns_metrics(client):
    headers = _auth_context(client)
    response = client.get("/api/v1/stats", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    metrics = {m["name"]: m["value"] for m in data[0]["metrics"]}
    assert "total_news" in metrics
    assert "total_sources" in metrics
    assert "total_alerts" in metrics
    assert all(isinstance(v, (int, float)) for v in metrics.values())


def test_stats_requires_auth(client):
    response = client.get("/api/v1/stats")
    assert response.status_code == 401


def test_stats_reflect_new_source(client):
    headers = _auth_context(client)

    before = {
        m["name"]: m["value"]
        for m in client.get("/api/v1/stats", headers=headers).json()[0]["metrics"]
    }

    client.post(
        "/api/v1/information-sources",
        headers=headers,
        json={"name": "Stats Source", "rss_url": f"https://example.com/rss/{uuid.uuid4()}"},
    )

    after = {
        m["name"]: m["value"]
        for m in client.get("/api/v1/stats", headers=headers).json()[0]["metrics"]
    }

    assert after["total_sources"] == before["total_sources"] + 1
