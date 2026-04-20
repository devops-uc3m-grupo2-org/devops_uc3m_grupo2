"""
Sprint 5 — Monitorización RSS y notificaciones.

Historia: el sistema revisa fuentes RSS, detecta noticias que coinciden con
los descriptores de una alerta y genera un enlace alerta-noticia (AlertNews).
Los tests verifican tanto la lógica de matching como el pipeline completo.
"""
import uuid
from datetime import datetime, timezone

from app.models.models import (
    Alert,
    AlertNews,
    Category,
    InformationSource,
    IPTCCategoryEnum,
    NewsItem,
    RSSChannel,
)
from app.services.alertLogic import match_alert
from app.core.scheduler import process_alerts_for_items


# --- Unidad: lógica de matching ---

def _make_alert(descriptors: list[str]) -> Alert:
    return Alert(
        name="test",
        descriptors=descriptors,
        categories=[],
        cron_expression="*/5 * * * *",
        is_active=True,
        user_id=1,
    )


def _make_news(title: str, summary: str = "") -> NewsItem:
    return NewsItem(title=title, link=f"https://example.com/{uuid.uuid4()}", summary=summary)


def test_match_alert_descriptor_in_title():
    assert match_alert(_make_alert(["tecnología"]), _make_news("Avance en tecnología de IA")) is True


def test_match_alert_descriptor_in_summary():
    assert match_alert(_make_alert(["economía"]), _make_news("Noticia sin relación", "Impacto en la economía global")) is True


def test_match_alert_no_match():
    assert match_alert(_make_alert(["fútbol"]), _make_news("Nuevo record en bolsa de valores")) is False


def test_match_alert_case_insensitive():
    assert match_alert(_make_alert(["Tecnología"]), _make_news("avance en tecnología")) is True


def test_match_alert_empty_descriptors():
    assert match_alert(_make_alert([]), _make_news("cualquier noticia")) is False


# --- Integración: pipeline alert → news → AlertNews ---

def test_monitoring_pipeline(client, session):
    """
    Pipeline completo:
    1. Crear usuario y alerta con descriptores vía API.
    2. Insertar fuente, canal y noticia directamente en la BD de test.
    3. Ejecutar process_alerts_for_items con la sesión de test.
    4. Verificar que se creó el registro AlertNews.
    5. Confirmar que los endpoints de notificaciones responden correctamente.
    """
    email = f"monitor_{uuid.uuid4()}@mail.com"
    password = "admin123"

    # 1a. Registro y login
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Monitor",
            "last_name": "Tester",
            "organization": "QA",
        },
    )
    assert reg.status_code == 200
    user_id = reg.json()["id"]

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 1b. Crear alerta con descriptor "tecnología"
    alert_resp = client.post(
        f"/api/v1/users/{user_id}/alerts",
        headers=headers,
        json={
            "name": "Alerta Tecnología",
            "descriptors": ["tecnología"],
            "categories": [],
            "cron_expression": "*/5 * * * *",
            "is_active": True,
        },
    )
    assert alert_resp.status_code == 201
    alert_id = alert_resp.json()["id"]

    # 2. Insertar fuente, canal y noticia directamente en la sesión de test
    source = InformationSource(
        name="Fuente Test", rss_url=f"https://rss.example.com/{uuid.uuid4()}"
    )
    session.add(source)
    session.flush()

    category = Category(name=IPTCCategoryEnum.SCIENCE_AND_TECHNOLOGY, source="IPTC")
    session.add(category)
    session.flush()

    channel = RSSChannel(
        url=source.rss_url,
        information_source_id=source.id,
        category_id=category.id,
    )
    session.add(channel)
    session.flush()

    news_item = NewsItem(
        title="Gran avance en tecnología de inteligencia artificial",
        link=f"https://example.com/news/{uuid.uuid4()}",
        summary="La tecnología IA transforma el sector sanitario",
        published=datetime.now(timezone.utc),
        channel_id=channel.id,
    )
    session.add(news_item)
    session.flush()

    # 3. Ejecutar el motor de matching del scheduler
    process_alerts_for_items(session, [news_item])

    # 4. Verificar que se enlazó la alerta con la noticia
    alert_news = (
        session.query(AlertNews)
        .filter_by(alert_id=alert_id, news_item_id=news_item.id)
        .first()
    )
    assert alert_news is not None, "El motor de alertas debería haber creado un AlertNews"

    # 5. Los endpoints de notificaciones del usuario funcionan
    notif_list = client.get(
        f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications",
        headers=headers,
    )
    assert notif_list.status_code == 200
    assert isinstance(notif_list.json(), list)

    # Crear una notificación (simula lo que haría el scheduler tras el match)
    notif_create = client.post(
        f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications",
        headers=headers,
        json={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": [{"name": "news_matched", "value": 1}],
        },
    )
    assert notif_create.status_code == 201
    assert notif_create.json()["metrics"][0]["value"] == 1
