from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.models.models import RSSChannel
from app.services.fetcher import fetch_feed
from app.services.alertLogic import process_alerts_for_items

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

        if oncomingNews:
            process_alerts_for_items(db, oncomingNews)
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        fetch_all_sources_job,
        trigger="cron",
        minute="*/5",
        max_instances=1,
        misfire_grace_time=60,
    )

    scheduler.start()