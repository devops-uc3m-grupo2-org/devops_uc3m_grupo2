import uuid

def test_create_source_ok(client):
    response = client.post(
        "/api/v1/sources",
        json={
            "name": "Test Source",
            "medium": "web",
            "rss_url": f"https://example.com/rss/{uuid.uuid4()}",
            "iptc_category": "tech"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Source"


def test_create_source_duplicate(client):
    rss_url = f"https://example.com/rss/{uuid.uuid4()}"

    client.post(
        "/api/v1/sources",
        json={"name": "Source1", "rss_url": rss_url}
    )

    response = client.post(
        "/api/v1/sources",
        json={"name": "Source2", "rss_url": rss_url}
    )

    assert response.status_code == 409


def test_list_sources(client):
    response = client.get("/api/v1/sources")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_fetch_source_not_found(client):
    response = client.post("/api/v1/sources/999999/fetch")

    assert response.status_code == 404


def test_fetch_source_debug(client):
    # Crear source primero
    response = client.post(
        "/api/v1/sources",
        json={
            "name": "Debug Source",
            "rss_url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
        }
    )

    source_id = response.json()["id"]

    response = client.post(f"/api/v1/sources/{source_id}/fetch?debug=true")

    assert response.status_code == 200
    data = response.json()
    assert "entries_count" in data