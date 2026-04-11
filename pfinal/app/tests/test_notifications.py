from app.models.models import Notification
from app.services.notifications import notify_user, create_notification

#Test capa DB, no de endpoint
def test_create_notification(session, create_user, create_news, create_alert, create_source):
    user = create_user

    from app.models.models import InformationSource

    source = create_source
    news = create_news(source.id)
    alert = create_alert(user.id)

    create_notification(session, alert, news)
    session.commit()

    from app.models.models import Notification
    notifications = session.query(Notification).all()

    assert len(notifications) == 1
    assert notifications[0].user_id == user.id
    assert notifications[0].news_item_id == news.id

#Endpoint test
def test_list_notification(
    client,
    session,
    create_user,
    create_news,
    create_alert,
    create_source
):
    user = create_user
    source = create_source

    news = create_news(source.id)
    alert = create_alert(user.id)

    from app.models.models import Notification
    notification = Notification(
        alert_id=alert.id,
        news_item_id=news.id,
        user_id=user.id,
        subject="Test subject",
        body="Test body",
        status="pending"
    )

    session.add(notification)
    session.commit()

    response = client.get("/api/v1/get-notifications")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1

    assert data[0]["user_id"] == user.id
    assert data[0]["subject"] == "Test subject"
    assert data[0]["status"] == "pending"