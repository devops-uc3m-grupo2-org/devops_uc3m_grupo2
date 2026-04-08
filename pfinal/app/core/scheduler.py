from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.models.models import InformationSource, NewsItem, Alert, AlertNews, Notification
from app.services.fetcher import fetch_feed
from app.services.notifications import notify_user, build_email_body
from app.services.alertLogic import match_alert
import datetime

scheduler = BackgroundScheduler()


def fetch_all_sources_job():
    db = SessionLocal()

    try:
        sources = db.query(InformationSource).all()
        oncomingNews= []
        for source in sources:
            try:
                n_new_items, items = fetch_feed(db, source.id, limit=10) #Limitado a 10 par efectos de debugging
                oncomingNews.extend(items)

                print(f"[FETCH] Source {source.id}: {n_new_items} new items")
            except Exception as e:
                print(f"[ERROR] Source {source.id}: {e}")
        
        process_alerts_for_items(db, oncomingNews)

    finally:
        db.close()

def process_alerts_for_items(db, items):
    alerts = db.query(Alert).filter(Alert.is_active == True).all()
    try:
        for item in items:
            for alert in alerts:
                if match_alert(alert, item):
                    print(f"[MATCH] Alert {alert.id} matched News {item.id}") #Para Debugging, puede ser removido más tarde
                    exists = db.query(AlertNews).filter_by(
                            alert_id = alert.id,
                            news_item_id = item.id).first()

                    if not exists:
                        alert_new= AlertNews(
                            alert_id=alert.id,
                            news_item_id=item.id)
                        db.add(alert_new)

                        notification = Notification(
                            alert_id=alert.id,
                            news_item_id=item.id,
                            user_id=alert.user_id,
                            subject=f"Actualización de {alert.name}",
                            body=build_email_body(alert, item),
                            status="pending")
                        db.add(notification)
                else:
                    print(f"[NO MATCH] Alert {alert.id} No matched News") #Para Debugging, puede ser removido más tarde

        notify_user(db)
        db.commit()

        notify_user(db)
    except Exception as e:
        db.rollback()
        raise e


def start_scheduler():
    scheduler.add_job(
        fetch_all_sources_job,
        trigger="cron",
        minute="*/5",
        max_instances=1
    )

    scheduler.start()