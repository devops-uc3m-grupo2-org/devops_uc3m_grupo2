import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
        db.rollback()
    finally:
        db.close()


@pytest.fixture
def client():
    def override_get_db():
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def create_news(db_session):
    from app.models.models import NewsItem

    def _create(source_id):
        news = NewsItem(
            title="Madrid gana el partido",
            summary="Deportes en Madrid",
            link="http://test.com",
            source_id=source_id
        )
        db_session.add(news)
        db_session.commit()
        db_session.refresh(news)
        return news

    return _create