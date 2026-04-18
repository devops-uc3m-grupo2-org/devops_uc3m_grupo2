from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.models.models import InformationSource, RSSChannel, NewsItem, Alert, AlertNews
from app.services.fetcher import fetch_feed
from app.services.notifications import notify_user
from app.services.alertLogic import match_alert

scheduler = BackgroundScheduler()


def fetch_all_sources_job():
    db = SessionLocal()

    try:
        channels = db.query(RSSChannel).all()
        oncomingNews = []
        for channel in channels:
            try:
                n_new_items, items = fetch_feed(db, channel.id, limit=10)  # Limitado a 10 para debugging
                oncomingNews.extend(items)

                print(f"[FETCH] Channel {channel.id}: {n_new_items} new items")
            except Exception as e:
                print(f"[ERROR] Channel {channel.id}: {e}")
        
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
                        db.add(AlertNews(
                            alert_id=alert.id,
                            news_item_id=item.id))
                    notify_user(alert)
                else:
                    print(f"[NO MATCH] Alert {alert.id} No matched News") #Para Debugging, puede ser removido más tarde
        db.commit()
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