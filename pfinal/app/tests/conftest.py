import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SEND_EMAILS", "false")

from app.main import app
from app.core.database import Base, engine, get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    from sqlalchemy.orm import Session as SASession
    from app.models.models import Role as RoleModel, User as UserModel
    from passlib.context import CryptContext

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Seed roles y admin (necesarios para los tests con role_ids)
    pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    with SASession(engine) as db:
        if db.query(RoleModel).count() == 0:
            db.add_all([RoleModel(name="admin"), RoleModel(name="user")])
            db.commit()
        if db.query(UserModel).count() == 0:
            admin_role = db.query(RoleModel).filter(RoleModel.name == "admin").first()
            db.add(UserModel(
                email="admin@newsradar.com",
                first_name="Admin",
                last_name="NewsRadar",
                organization="NewsRadar",
                hashed_password=pwd.hash("admin123"),
                roles=[admin_role],
            ))
            db.commit()

    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def session():
    from app.core.database import SessionLocal

    # Crea enlace con la base de datos
    connection = engine.connect()
    # Todo lo que haga ahora es temporal
    transaction = connection.begin()

    db = SessionLocal(bind=connection)
    #Comparte la sesión con los tests
    yield db
    # Evita que los cambios persistan en los tests.
    transaction.rollback()
    connection.close()

    # Cierra Conexión
    db.close()
        
@pytest.fixture
def client(session):
    def override_get_db():
        yield session
    #Usa una sesión local en vez de la base de datos PosgreSQL real
    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)
    #aislamiento
    app.dependency_overrides.clear()


@pytest.fixture
def create_news(session):
    from app.models.models import NewsItem
    #Simula una noticia en la base de datos.
    def _create(source_id):
        news = NewsItem(
            title="Madrid gana el partido",
            summary="Deportes en Madrid",
            link="http://test.com",
            source_id=source_id
        )
        #Se crea la noticia en la BD de la sesión
        session.add(news)
        session.commit()
        session.refresh(news)
        return news

    return _create

@pytest.fixture
def create_user(session):
    from app.models.models import User
    n_user = User(id= 1,
        email= "prueba@gmail.com",
        first_name= "prueba",
        last_name= "pruebas",
        organization= "si",
        hashed_password="ABCDEFGH"
    )
    session.add(n_user)
    session.commit()
    session.refresh(n_user)
    return n_user
    
