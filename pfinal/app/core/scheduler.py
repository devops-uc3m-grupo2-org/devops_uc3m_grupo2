from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.models.models import InformationSource
from app.services.fetcher import fetch_feed

scheduler = BackgroundScheduler()


def fetch_all_sources_job():
    db = SessionLocal()

    try:
        sources = db.query(InformationSource).all()

        for source in sources:
            try:
                new_items = fetch_feed(db, source.id, limit=10)
                print(f"[FETCH] Source {source.id}: {new_items} new items")
            except Exception as e:
                print(f"[ERROR] Source {source.id}: {e}")

    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        fetch_all_sources_job,
        "interval",
        minutes=5,
        max_instances=1
    )

    scheduler.start()