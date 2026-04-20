import uuid


def _auth_context(client):
    email = f"sources_{uuid.uuid4()}@mail.com"
    password = "admin123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Sources",
            "last_name": "Tester",
            "organization": "QA",
        },
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_source_ok(client):
    headers = _auth_context(client)
    response = client.post(
        "/api/v1/information-sources",
        headers=headers,
        json={
            "name": "Test Source",
            "medium": "web",
            "rss_url": f"https://example.com/rss/{uuid.uuid4()}",
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Source"


def test_create_source_duplicate(client):
    headers = _auth_context(client)
    rss_url = f"https://example.com/rss/{uuid.uuid4()}"

    client.post(
        "/api/v1/information-sources",
        headers=headers,
        json={"name": "Source1", "rss_url": rss_url}
    )

    response = client.post(
        "/api/v1/information-sources",
        headers=headers,
        json={"name": "Source2", "rss_url": rss_url}
    )

    assert response.status_code == 409


def test_list_sources(client):
    headers = _auth_context(client)

    created_source = client.post(
        "/api/v1/information-sources",
        headers=headers,
        json={
            "name": "Test Source",
            "rss_url": f"https://test.com/rss/{uuid.uuid4()}",
            "medium": "web"
        }
    )

    assert created_source.status_code == 201

    source_data = created_source.json()

    response = client.get("/api/v1/information-sources", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    sources = response.json()
    assert any(s["id"] == source_data["id"] for s in sources)


def test_fetch_source_not_found(client):
    headers = _auth_context(client)
    response = client.post("/api/v1/information-sources/999999/fetch", headers=headers)

    assert response.status_code == 404


def test_fetch_source_debug(client):
    headers = _auth_context(client)

    response = client.post(
        "/api/v1/information-sources",
        headers=headers,
        json={
            "name": "Debug Source",
            "rss_url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
        }
    )

    source_id = response.json()["id"]

    response = client.post(
        f"/api/v1/information-sources/{source_id}/fetch?debug=true",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "entries_count" in data
