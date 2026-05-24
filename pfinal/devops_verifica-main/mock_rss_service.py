import argparse
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from threading import Lock
from typing import List

from fastapi import FastAPI, Response
import uvicorn

app = FastAPI(title="Mock RSS News API")

_invocation_count = 0
_next_news_id = 1
_invocation_lock = Lock()


def _next_batch_metadata() -> tuple[int, int]:
    global _invocation_count, _next_news_id
    with _invocation_lock:
        _invocation_count += 1
        if _invocation_count == 1:
            batch_size = 5
        elif _invocation_count == 2:
            batch_size = 3
        else:
            batch_size = 0

        start_id = _next_news_id
        _next_news_id += batch_size
        return batch_size, start_id


def _build_items(count: int, start_id: int) -> List[dict]:
    now = datetime.now(timezone.utc)
    items: List[dict] = []
    for i in range(start_id, start_id + count):
        pub_date = now - timedelta(minutes=i)
        items.append(
            {
                "title": f"Noticia sintetica {i}",
                "description": f"Resumen sintetico de la noticia {i} para pruebas de RSS.",
                "link": f"https://example.com/news/{i}",
                "guid": f"mock-news-{i}-{int(pub_date.timestamp())}",
                "pub_date": format_datetime(pub_date),
            }
        )
    return items


def _build_rss_xml(items: List[dict]) -> str:
    item_xml = "".join(
        (
            "<item>"
            f"<title>{item['title']}</title>"
            f"<description>{item['description']}</description>"
            f"<link>{item['link']}</link>"
            f"<guid>{item['guid']}</guid>"
            f"<pubDate>{item['pub_date']}</pubDate>"
            "</item>"
        )
        for item in items
    )

    now = format_datetime(datetime.now(timezone.utc))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0">'
        "<channel>"
        "<title>Mock DevOps News Radar</title>"
        "<description>Feed RSS sintetico para pruebas.</description>"
        "<link>https://example.com/news</link>"
        f"<lastBuildDate>{now}</lastBuildDate>"
        f"{item_xml}"
        "</channel>"
        "</rss>"
    )


@app.get("/rss")
def generate_rss() -> Response:
    item_count, start_id = _next_batch_metadata()
    rss_xml = _build_rss_xml(_build_items(item_count, start_id))
    return Response(content=rss_xml, media_type="application/rss+xml")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mock RSS News API")
    parser.add_argument("--host", default="127.0.0.1", help="Host de escucha")
    parser.add_argument("--port", type=int, default=8000, help="Puerto de escucha")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Activa autoreload para desarrollo",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    uvicorn.run("mock_rss_service:app", host=args.host, port=args.port, reload=args.reload)
