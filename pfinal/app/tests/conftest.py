import pytest
from fastapi.testclient import TestClient
from app.main import create_seed_data

from app.main import app
from app.core.database import Base, engine

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Crear tablas antes de los tests
    Base.metadata.create_all(bind=engine)
    create_seed_data()
    yield
    # (opcional) borrar después
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)
