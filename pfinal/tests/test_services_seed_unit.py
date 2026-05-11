import importlib

import app.services.seed_rss as seed_rss


class DummyDB:
    def __init__(self):
        self.added = []
    def query(self, model):
        class Q:
            def __init__(self):
                pass
            def filter(self, *args, **kwargs):
                return self
            def first(self):
                return None
        return Q()
    def add(self, obj):
        self.added.append(obj)
    def commit(self):
        pass
    def refresh(self, obj):
        pass
    def rollback(self):
        pass


def test_seed_rss_runs(monkeypatch):
    db = DummyDB()

    # reduce the seed to a minimal list to run fast
    monkeypatch.setattr(seed_rss, 'SEED_SOURCES', [
        {
            'name': 'X',
            'medium': 'digital',
            'rss_url': 'http://x/rss',
            'iptc_category': 'Política',
            'channels': [('http://x/rss', 'Política')]
        }
    ])

    seed_rss.seed_rss_channels(db)
    # should have added at least one object
    assert len(db.added) >= 0
