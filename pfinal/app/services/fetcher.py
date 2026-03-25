import time
from datetime import datetime
import feedparser

from sqlalchemy.orm import Session

from app.models.models import InformationSource, NewsItem


def fetch_feed(db: Session, source_id: int, limit: int = 10) -> int:
    src = db.query(InformationSource).get(source_id)
    if not src:
        raise ValueError("Fuente no encontrada")

    feed = feedparser.parse(src.rss_url)
    created = 0
    for entry in feed.entries[:limit]:
        link = getattr(entry, "link", None) or getattr(entry, "id", None)
        if not link:
            continue
        if db.query(NewsItem).filter(NewsItem.link == link).first():
            continue

        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            except Exception:
                published = None

        item = NewsItem(
            title=getattr(entry, "title", ""),
            link=link,
            summary=getattr(entry, "summary", ""),
            published=published,
            source_id=src.id,
        )
        db.add(item)
        created += 1

    db.commit()
    return created
