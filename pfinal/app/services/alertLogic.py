import re
from app.models.models import Alert, AlertNews, Notification
from app.services.notifications import notify_user


def match_alert(alert, news_item):
    text = ((news_item.title or "") + " " + (news_item.summary or "")).lower()
    for descriptor in (alert.descriptors or []):
        if not descriptor:
            continue
        descriptor_text = descriptor.strip().lower()
        if not descriptor_text:
            continue
        pattern = re.escape(descriptor_text)
        if re.search(rf"\b{pattern}\b", text, flags=re.UNICODE):
            return True
    return False


def process_alerts_for_items(db, news_items):
    if not news_items:
        return

    alerts = db.query(Alert).filter(Alert.is_active == True).all()
    if not alerts:
        return

    try:
        for item in news_items:
            for alert in alerts:
                if match_alert(alert, item):
                    already = db.query(AlertNews).filter(
                        AlertNews.alert_id == alert.id,
                        AlertNews.news_item_id == item.id,
                    ).first()
                    if already:
                        continue

                    db.add(AlertNews(alert_id=alert.id, news_item_id=item.id))
                    db.add(Notification(alert_id=alert.id, metrics=[{"name": "news_matched", "value": 1}]))
                    notify_user(alert, item)
        db.commit()
    except Exception:
        db.rollback()
        raise
