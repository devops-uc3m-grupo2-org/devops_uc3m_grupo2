from apscheduler.schedulers.background import BackgroundScheduler
from app.services.fetcher import fetch_all_sources

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(fetch_all_sources, "interval", minutes=5)
    scheduler.start()