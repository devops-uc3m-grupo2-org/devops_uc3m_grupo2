from app.models.models import Alert, AlertNews, Notification


def match_alert(alert, news_item):
    text = (news_item.title + " " + (news_item.summary or "")).lower()
    keywords = [d.lower() for d in (alert.descriptors or [])]
    return any(k in text for k in keywords)


def process_alerts_for_items(db, news_items):
    if not news_items:
        return
    alerts = db.query(Alert).filter(Alert.is_active == True).all()
    triggered = set()
    for alert in alerts:
        for item in news_items:
            if match_alert(alert, item):
                already = db.query(AlertNews).filter(
                    AlertNews.alert_id == alert.id,
                    AlertNews.news_item_id == item.id,
                ).first()
                if not already:
                    db.add(AlertNews(alert_id=alert.id, news_item_id=item.id))
                    triggered.add(alert.id)
    # Una notificación por alerta que se disparó en este batch
    for alert_id in triggered:
        db.add(Notification(alert_id=alert_id, metrics=[]))
    db.commit()
