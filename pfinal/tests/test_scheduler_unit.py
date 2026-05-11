import app.core.scheduler as scheduler_mod


def test_fetch_all_sources_job_handles_empty(monkeypatch):
    class DummyQuery:
        def __init__(self, items=None):
            self._items = items or []
        def all(self):
            return self._items

    class DummyDB:
        def query(self, model):
            return DummyQuery([])
        def close(self):
            pass

    monkeypatch.setattr(scheduler_mod, 'SessionLocal', lambda: DummyDB())
    # ensure fetch_feed is a no-op to avoid network/DB side-effects
    monkeypatch.setattr(scheduler_mod, 'fetch_feed', lambda db, channel_id, limit=10: None)
    # just call the function to ensure it doesn't raise
    scheduler_mod.fetch_all_sources_job()
