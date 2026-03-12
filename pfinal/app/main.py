from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from app.core.database import engine, Base, get_db
from app.models.models import User, Role

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
