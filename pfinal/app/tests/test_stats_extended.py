import uuid


def _auth(client):
    email = f"stx_{uuid.uuid4()}@mail.com"
    password = "admin123"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": password,
        "first_name": "StatsX", "last_name": "Tester",
        "organization": "QA", "role_ids": [1],
    })
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _get_user_id(client, headers):
    users = client.get("/api/v1/users", headers=headers).json()
    me_email = client.post("/api/v1/auth/login").json() if False else None
    # Get the most recently created user (ourselves)
    return users[-1]["id"]


def test_stats_by_category_requires_auth(client):
    response = client.get("/api/v1/stats/by-category")
    assert response.status_code == 401


def test_stats_by_category_empty(client):
    headers = _auth(client)
    response = client.get("/api/v1/stats/by-category", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_wordcloud_requires_auth(client):
    response = client.get("/api/v1/stats/wordcloud")
    assert response.status_code == 401


def test_wordcloud_empty_no_alerts(client):
    headers = _auth(client)
    response = client.get("/api/v1/stats/wordcloud", headers=headers)
    assert response.status_code == 200
    assert response.json() == {}


def test_stats_by_category_with_alert(client):
    headers = _auth(client)
    users = client.get("/api/v1/users", headers=headers).json()
    user_id = users[-1]["id"]

    client.post(f"/api/v1/users/{user_id}/alerts", headers=headers, json={
        "name": "test cat alert",
        "descriptors": ["python"],
        "categories": [{"code": "01", "label": "Ciencia"}],
        "rss_channels_ids": [],
        "information_sources_ids": [],
        "cron_expression": "0 * * * *",
        "is_active": True,
    })

    response = client.get("/api/v1/stats/by-category", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    labels = [item["category"] for item in data]
    assert "Ciencia" in labels


def test_alert_limit_enforced(client):
    headers = _auth(client)
    users = client.get("/api/v1/users", headers=headers).json()
    user_id = users[-1]["id"]

    def make_alert(i):
        return client.post(f"/api/v1/users/{user_id}/alerts", headers=headers, json={
            "name": f"alert_{i}",
            "descriptors": [f"kw{i}"],
            "categories": [],
            "rss_channels_ids": [],
            "information_sources_ids": [],
            "cron_expression": "0 * * * *",
            "is_active": True,
        })

    # Create up to 20 alerts
    for i in range(20):
        r = make_alert(i)
        assert r.status_code == 201

    # 21st should be rejected
    response = make_alert(20)
    assert response.status_code == 422


def test_alerts_check_endpoint(client):
    headers = _auth(client)
    response = client.post("/api/v1/alerts/check", headers=headers)
    assert response.status_code == 200
