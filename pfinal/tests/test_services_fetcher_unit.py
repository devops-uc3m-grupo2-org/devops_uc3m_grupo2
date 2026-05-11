from types import SimpleNamespace
import importlib

import app.services.fetcher as fetcher


class FakeQuery:
    def __init__(self, channel):
        self.channel = channel

    def get(self, _id):
        if self.channel.id == _id:
            return self.channel
        return None

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None


class FakeDB:
    def __init__(self, channel):
        self.channel = channel
        self.added = []

    def query(self, model):
        return FakeQuery(self.channel)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass


class FakeEntry:
    def __init__(self, link, title="t", summary="s"):
        self.link = link
        self.title = title
        self.summary = summary


def test_fetch_feed_creates_items(monkeypatch):
    channel = SimpleNamespace(id=1, url="http://example.com/rss")
    db = FakeDB(channel)

    fake_feed = SimpleNamespace(entries=[FakeEntry("http://a/1"), FakeEntry("http://a/2")])

    monkeypatch.setattr(fetcher, "feedparser", SimpleNamespace(parse=lambda url: fake_feed))

    created, items = fetcher.fetch_feed(db, channel_id=1, limit=10)

    assert created == 2
    assert len(items) == 2
    assert items[0].link == "http://a/1"
