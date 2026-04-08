from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.models.models import InformationSource, NewsItem, Alert, AlertNews
from app.services.fetcher import fetch_feed
from app.services.notifications import notify_user
from app.services.alertLogic import match_alert

scheduler = BackgroundScheduler()


def fetch_all_sources_job():
    db = SessionLocal()

    try:
        sources = db.query(InformationSource).all()

        for source in sources:
            try:
                n_new_items = fetch_feed(db, source.id, limit=10) #Limitado a 10 par efectos de debugging
                items = db.query(NewsItem).order_by(NewsItem.id.desc()).limit(n_new_items).all() #Los últimos introducidos

                process_alerts_for_items(db, items)

                print(f"[FETCH] Source {source.id}: {n_new_items} new items")
            except Exception as e:
                print(f"[ERROR] Source {source.id}: {e}")

    finally:
        db.close()

def process_alerts_for_items(db, items):
    alerts = db.query(Alert).filter(Alert.is_active == True).all()

    for item in items:
        for alert in alerts:
            if match_alert(alert, item):
                print(f"[MATCH] Alert {alert.id} matched News {item.id}")
                exists = db.query(AlertNews).filter_by(
                        alert_id = alert.id,
                        news_item_id = item.id).first()

                if not exists:
                    db.add(AlertNews(
                        alert_id=alert.id,
                        news_item_id=item.id))
                notify_user(alert)


def start_scheduler():
    scheduler.add_job(
        fetch_all_sources_job,
        trigger="cron",
        minute="*/5",
        max_instances=1
    )

    scheduler.start()