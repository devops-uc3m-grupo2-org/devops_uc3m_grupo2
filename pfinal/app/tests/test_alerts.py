def test_create_alert(client, create_user):
    user = create_user
    response = client.post(
        "/api/v1/alerts",
        json={
            "name": "Bitcoin Alert",
            "keyword": "bitcoin",
            "iptc_category": "Economía, negocios y finanzas",
            "user_id": user.id,
            "synonyms": ["btc", "crypto"]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["keyword"] == "bitcoin"
    assert "btc" in data["synonyms"]


def test_create_and_list_alerts(client, create_user):
    user = create_user
    client.post(
        "/api/v1/alerts",
        json={
            "name": "Bitcoin Alert",
            "keyword": "bitcoin",
            "iptc_category": "Economía, negocios y finanzas",
            "user_id": user.id,
            "synonyms": ["btc", "crypto"]
        }
    )

    response = client.get("/api/v1/alerts")

    assert response.status_code == 200

    alerts = response.json()

    assert any(a["keyword"] == "bitcoin" for a in alerts)


def test_update_alert(client, create_user):
    user = create_user
    # Crear alerta
    create = client.post(
        "/api/v1/alerts",
        json={
            "name": "Test Alert",
            "keyword": "ai",
            "iptc_category": "Ciencias y tecnología",
            "user_id": user.id
        }
    )

    alert_id = create.json()["id"]

    response = client.put(
        f"/api/v1/alerts/{alert_id}",
        json={"name": "Updated Alert", "is_active": False}
    )

    assert response.status_code == 200


def test_update_alert_persists(client, create_user):
    user = create_user
    create = client.post(
        "/api/v1/alerts",
        json={
            "name": "Old Name",
            "keyword": "ai",
            "iptc_category": "Ciencias y Tecnología",
            "user_id": user.id
        }
    )

    alert_id = create.json()["id"]

    client.put(
        f"/api/v1/alerts/{alert_id}",
        json={"name": "New Name"}
    )

    response = client.get("/api/v1/alerts")
    alerts = response.json()

    updated = next(a for a in alerts if a["id"] == alert_id)

    assert updated["name"] == "New Name"

def test_create_and_delete_alert(client, create_user):
    user = create_user
    create = client.post(
        "/api/v1/alerts",
        json={
            "name": "Delete Alert",
            "keyword": "delete",
            "iptc_category": "deportes",
            "user_id": user.id
        }
    )

    alert_id = create.json()["id"]

    client.delete(f"/api/v1/alerts/{alert_id}")

    response = client.get("/api/v1/alerts")
    alerts = response.json()

    assert all(a["id"] != alert_id for a in alerts)


def test_delete_alert_not_found(client):
    response = client.delete("/api/v1/alerts/999999")

    assert response.status_code == 404

def test_run_matching_creates_relations(client, create_news, create_user, create_source):
    user = create_user
    source = create_source

    alert = client.post(
        "/api/v1/alerts",
        json={
            "name": "AMNews",
            "keyword": "Madrid",
            "iptc_category": "Deportes",
            "user_id": user.id,
            "is_active": True
        }
    ).json()

    create_news(source.id)

    client.post("/api/v1/run-matching")

    response = client.get(f"/api/v1/matchAlert/{alert['id']}")

    assert response.status_code == 200
    assert len(response.json()["news_ids"]) > 0


def test_alert_match_not_found(client):
    
    response = client.get("/api/v1/matchAlert/999999")

    assert response.status_code == 404