import uuid

from app.models.models import IPTCCategoryEnum


def _auth_context(client):
    email = f"alerts_{uuid.uuid4()}@mail.com"
    password = "admin123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Alerts",
            "last_name": "Tester",
            "organization": "QA",
            "role_ids": [1],
        },
    )
    assert register_response.status_code == 200

    user_id = register_response.json()["id"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return user_id, headers


def test_alert_crud_for_user(client):
    user_id, headers = _auth_context(client)

    create_response = client.post(
        f"/api/v1/users/{user_id}/alerts",
        headers=headers,
        json={
            "name": "Alerta tecnologia",
            "descriptors": ["tecnologia", "IA", "startups"],
            "categories": [
                {
                    "code": IPTCCategoryEnum.SCIENCE_AND_TECHNOLOGY.value,
                    "label": IPTCCategoryEnum.SCIENCE_AND_TECHNOLOGY.value,
                }
            ],
            "cron_expression": "*/5 * * * *",
            "is_active": True,
        },
    )

    assert create_response.status_code == 201
    alert = create_response.json()
    alert_id = alert["id"]
    assert alert["name"] == "Alerta tecnologia"
    assert alert["user_id"] == user_id

    list_response = client.get(f"/api/v1/users/{user_id}/alerts", headers=headers)
    assert list_response.status_code == 200
    alerts = list_response.json()
    assert any(item["id"] == alert_id for item in alerts)

    detail_response = client.get(
        f"/api/v1/users/{user_id}/alerts/{alert_id}",
        headers=headers,
    )
    assert detail_response.status_code == 200

    update_response = client.put(
        f"/api/v1/users/{user_id}/alerts/{alert_id}",
        headers=headers,
        json={
            "name": "Alerta tecnologia actualizada",
            "descriptors": ["tecnologia", "innovacion"],
            "is_active": False,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Alerta tecnologia actualizada"
    assert update_response.json()["is_active"] is False

    delete_response = client.delete(
        f"/api/v1/users/{user_id}/alerts/{alert_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    missing_response = client.get(
        f"/api/v1/users/{user_id}/alerts/{alert_id}",
        headers=headers,
    )
    assert missing_response.status_code == 404


def test_notification_crud_for_alert(client):
    user_id, headers = _auth_context(client)

    create_alert_response = client.post(
        f"/api/v1/users/{user_id}/alerts",
        headers=headers,
        json={
            "name": "Alerta notificaciones",
            "descriptors": ["finanzas"],
            "categories": [
                {
                    "code": IPTCCategoryEnum.ECONOMY_BUSINESS_AND_FINANCE.value,
                    "label": IPTCCategoryEnum.ECONOMY_BUSINESS_AND_FINANCE.value,
                }
            ],
            "cron_expression": "*/10 * * * *",
            "is_active": True,
        },
    )
    assert create_alert_response.status_code == 201
    alert_id = create_alert_response.json()["id"]

    create_notification_response = client.post(
        f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications",
        headers=headers,
        json={
            "timestamp": "2026-04-18T12:30:00Z",
            "metrics": [{"name": "news_matched", "value": 5}],
        },
    )
    assert create_notification_response.status_code == 201
    notification = create_notification_response.json()
    notification_id = notification["id"]
    assert notification["alert_id"] == alert_id

    list_notifications_response = client.get(
        f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications",
        headers=headers,
    )
    assert list_notifications_response.status_code == 200
    notifications = list_notifications_response.json()
    assert any(item["id"] == notification_id for item in notifications)

    detail_response = client.get(
        f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}",
        headers=headers,
    )
    assert detail_response.status_code == 200

    update_response = client.put(
        f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}",
        headers=headers,
        json={
            "metrics": [{"name": "news_matched", "value": 7}],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["metrics"][0]["value"] == 7

    delete_response = client.delete(
        f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    missing_response = client.get(
        f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}",
        headers=headers,
    )
    assert missing_response.status_code == 404
