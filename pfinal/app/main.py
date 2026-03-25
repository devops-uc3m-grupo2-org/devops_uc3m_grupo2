from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import Body

import os

from app.core.database import engine, Base, get_db
from app.models.models import User, Role, InformationSource, NewsItem
import feedparser
from app.services.fetcher import fetch_feed

load_dotenv()

app = FastAPI(title="NewsRadar API", version="1.0")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# Use pbkdf2_sha256 to avoid requiring the native bcrypt extension in the image
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# Crear tablas + seed al inicio
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    create_seed_data()

def create_seed_data():
    db = next(get_db())
    if db.query(Role).count() == 0:
        admin_role = Role(name="admin")
        user_role = Role(name="user")
        db.add_all([admin_role, user_role])
        db.commit()

    if db.query(User).count() == 0:
        admin = User(
            email="admin@newsradar.com",
            first_name="Admin",
            last_name="NewsRadar",
            organization="NewsRadar",
            hashed_password=pwd_context.hash("admin123")
        )
        db.add(admin)
        db.commit()

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/api/v1/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "message": "NewsRadar listo con PostgreSQL + JWT"}

# CRUD mínimo de usuarios (Fase 1)
@app.get("/api/v1/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "organization": u.organization,
        }
        for u in users
    ]

@app.post("/api/v1/auth/register")
def register(user_payload: dict, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_payload.get("email")).first():
        raise HTTPException(status_code=409, detail="El email ya está registrado")
    user = User(
        email=user_payload.get("email"),
        first_name=user_payload.get("first_name", ""),
        last_name=user_payload.get("last_name", ""),
        organization=user_payload.get("organization", ""),
        hashed_password=pwd_context.hash(user_payload.get("password", ""))
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "organization": user.organization,
    }


@app.post("/api/v1/sources")
def create_source(payload: dict = Body(...), db: Session = Depends(get_db)):
    if db.query(InformationSource).filter(InformationSource.rss_url == payload["rss_url"]).first():
        raise HTTPException(status_code=409, detail="La fuente ya existe")
    src = InformationSource(
        name=payload.get("name", "Fuente"),
        medium=payload.get("medium", ""),
        rss_url=payload["rss_url"],
        iptc_category=payload.get("iptc_category", ""),
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    return {"id": src.id, "name": src.name, "rss_url": src.rss_url}

@app.get("/api/v1/sources")
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(InformationSource).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "medium": s.medium,
            "rss_url": s.rss_url,
            "iptc_category": s.iptc_category,
        }
        for s in sources
    ]


@app.post("/api/v1/sources/{source_id}/fetch")
def fetch_source(source_id: int, db: Session = Depends(get_db), debug: bool = False):
    # Modo debug: devuelve metadata del feed y primer entry para diagnóstico
    src = db.query(InformationSource).get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")

    if debug:
        feed = feedparser.parse(src.rss_url)
        first = None
        if len(feed.entries) > 0:
            e = feed.entries[0]
            first = {
                "title": getattr(e, "title", None),
                "link": getattr(e, "link", None),
                "published": getattr(e, "published", None),
            }
        return {
            "source_id": source_id,
            "feed_status": feed.get("status", None),
            "entries_count": len(feed.entries),
            "first_entry": first,
        }

    try:
        created = fetch_feed(db, source_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")
    return {"source_id": source_id, "new_items": created}


@app.get("/api/v1/news")
def list_news(db: Session = Depends(get_db)):
    items = db.query(NewsItem).order_by(NewsItem.published.desc()).limit(200).all()
    return [
        {
            "id": i.id,
            "title": i.title,
            "link": i.link,
            "summary": i.summary,
            "published": i.published.isoformat() if i.published else None,
            "source_id": i.source_id,
        }
        for i in items
    ]


@app.get("/_routes")
def debug_list_routes():
    return [
        {"path": r.path, "name": r.name, "methods": sorted(list(r.methods))}
        for r in app.routes
    ]
