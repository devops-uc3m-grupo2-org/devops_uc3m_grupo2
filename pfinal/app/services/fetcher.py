import time
from datetime import datetime
import feedparser
from sqlalchemy.orm import Session

# Importamos RSSChannel en lugar de InformationSource
from app.models.models import RSSChannel, NewsItem

def fetch_feed(db: Session, channel_id: int, limit: int = 10) -> tuple[int, list]:
    created_items = []
    # Consultamos el canal RSS específico en lugar de la fuente general
    channel = db.query(RSSChannel).get(channel_id)
    if not channel:
        raise ValueError("Canal RSS no encontrado")

    # Usamos '.url' que es el campo correcto según models.py
    feed = feedparser.parse(channel.url) 
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
            channel_id=channel.id, # Usamos channel_id que es lo que espera NewsItem
        )
        db.add(item)
        created_items.append(item)
        
        created += 1

    db.commit()
    return created, created_items