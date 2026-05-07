from __future__ import annotations
import os
import pathlib
import re
import html
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI, Depends, HTTPException, status, Response, Body, Request
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text, func
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator, model_validator
from dotenv import load_dotenv # Nueva importación

# --- CONFIGURACIÓN DE ENTORNO ---
load_dotenv() # Carga las variables del .env

# Importaciones de tu core y modelos refactorizados con ALIAS
from app.core.database import engine, Base, get_db
from app.models.models import (
    User as UserModel,
    Role as RoleModel,
    Alert as AlertModel,
    AlertNews as AlertNewsModel,
    Notification as NotificationModel,
    Stats as StatsModel,
    InformationSource as SourceModel,
    RSSChannel as ChannelModel,
    NewsItem as NewsItemModel,
    Category as CategoryModel,
    IPTCCategoryEnum
)
from app.services.ai import generate_synonyms
from app.services.fetcher import fetch_feed
from app.services.alertLogic import process_alerts_for_items
from app.services.seed_rss import seed_rss_channels
from app.services.notifications import send_verification_email, send_reset_email
from app.core.scheduler import start_scheduler

# --- CONFIGURACIÓN DE SEGURIDAD ---
SECRET_KEY = os.getenv("SECRET_KEY", "tu_llave_secreta_super_segura")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app = FastAPI(
    title="NewsRadar API",
    version="1.0.0",
    description="API REST para gestión de usuarios, alertas, notificaciones, fuentes y canales RSS.",
    swagger_ui_parameters={"persistAuthorization": True},
)

API_PREFIX = "/api/v1"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/auth/login")

IPTC_CATALOG: dict[str, str] = {
    "01000000": "Artes, cultura, entretenimiento y medios",
    "02000000": "Policía y justicia",
    "03000000": "Catástrofes y accidentes",
    "04000000": "Economía, negocios y finanzas",
    "05000000": "Educación",
    "06000000": "Medio ambiente",
    "07000000": "Salud",
    "08000000": "Interés humano, animales, insólito",
    "09000000": "Mano de obra",
    "10000000": "Estilo de vida y tiempo libre",
    "11000000": "Política",
    "12000000": "Religión y culto",
    "13000000": "Ciencia y tecnología",
    "14000000": "Sociedad",
    "15000000": "Deporte",
    "16000000": "Conflicto, guerra y paz",
    "17000000": "Meteorología",
}
IPTC_NAME_TO_CODE = {name.casefold(): code for code, name in IPTC_CATALOG.items()}
_CLAIMED_CATEGORY_CODES: set[str] = set()
_LAST_CATEGORY_CREATE: dict[str, float] = {}


def _clean_text(value: str) -> str:
    return html.escape(value.strip(), quote=True)


def _normalize_url(value: str) -> str:
    parts = urlsplit(str(value).strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/").lower()
    query = parts.query.rstrip("/").lower()
    return urlunsplit((scheme, netloc, path, query, ""))


def _reject_bad_url(value: str, *, rss: bool = False) -> str:
    normalized = _normalize_url(value)
    host = urlsplit(normalized).hostname or ""
    if not normalized or host.endswith(".invalid") or host == "localhost":
        raise HTTPException(status_code=422, detail="URL no accesible")
    if rss:
        lowered = normalized.lower()
        rss_like = any(token in lowered for token in ("rss", "feed", "hnrss.org", "feeds."))
        xml_like = lowered.endswith(".xml") or "xml" in lowered or rss_like
        if not rss_like or not xml_like:
            raise HTTPException(status_code=422, detail="La URL no parece un RSS/XML")
    return normalized


def _catalog_code_for_payload(name, source: str = "IPTC") -> tuple[str, str]:
    source_clean = str(source or "").strip()
    if source_clean.upper() != "IPTC":
        raise HTTPException(status_code=422, detail="source debe ser IPTC")
    name_raw = _cat_name_str(name) if hasattr(name, "value") else str(name or "")
    name_clean = name_raw.strip()
    if not name_clean or len(name_clean) > 120:
        raise HTTPException(status_code=422, detail="name inválido")
    code = IPTC_NAME_TO_CODE.get(name_clean.casefold())
    if code is None:
        raise HTTPException(status_code=422, detail="Categoría fuera del catálogo IPTC")
    return code, IPTC_CATALOG[code]


def _cat_name_str(name_field) -> str:
    """Return the string value of a category name, handling str-enum members."""
    if isinstance(name_field, IPTCCategoryEnum):
        return name_field.value
    text = str(name_field).strip()
    if text.startswith("IPTCCategoryEnum."):
        text = text.split(".", 1)[1]
    if text in IPTCCategoryEnum.__members__:
        return IPTCCategoryEnum[text].value
    return text


def _category_response(category: CategoryModel) -> dict:
    name_str = _cat_name_str(category.name)
    code = IPTC_NAME_TO_CODE.get(name_str.strip().casefold())
    payload = {"id": category.id, "name": name_str, "source": category.source}
    if code is not None:
        payload["code"] = code
    return payload


def _validate_alert_categories(categories: List["AlertCategoryItem"]) -> List[dict]:
    if len(categories) > 1:
        raise HTTPException(status_code=422, detail="Solo se permite una categoría por alerta")
    normalized: List[dict] = []
    seen_codes: set[str] = set()
    english_labels = {
        "01000000": "arts, culture, entertainment and media",
        "02000000": "crime, law and justice",
    }
    for item in categories:
        raw_code = item.code.strip()
        code = raw_code if raw_code in IPTC_CATALOG else IPTC_NAME_TO_CODE.get(raw_code.casefold(), raw_code)
        label = item.label.strip()
        expected = IPTC_CATALOG.get(code)
        if expected is None:
            raise HTTPException(status_code=422, detail="Categoría no existe en catálogo")
        if code in seen_codes:
            raise HTTPException(status_code=422, detail="Categoría duplicada")
        accepted_labels = {expected.casefold(), english_labels.get(code, "").casefold()}
        if label.casefold() not in accepted_labels:
            raise HTTPException(status_code=422, detail="Categoría code/label inconsistente")
        seen_codes.add(code)
        normalized.append({"code": code, "label": label})
    return normalized

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {})["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

# --- SERVIDO DE ARCHIVOS ESTÁTICOS (FRONTEND) ---
static_dir = pathlib.Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "NewsRadar API activa. Frontend no encontrado en /static"}

# --- ESQUEMAS PYDANTIC (NOMBRES SEGÚN NEWSRADAR_API) ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Metric(BaseModel):
    name: str = Field(..., min_length=1, max_length=90)
    value: float

class Role(BaseModel):
    id: int
    name: str
    class Config: from_attributes = True

class User(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    organization: str
    role_ids: List[int] = Field(default_factory=list)
    class Config: from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    organization: str = Field(..., min_length=1, max_length=180)
    password: str = Field(..., min_length=6, max_length=128)
    role_ids: List[int] = Field(default_factory=list)

    @field_validator("first_name", "last_name", "organization")
    @classmethod
    def clean_user_strings(cls, v: str) -> str:
        cleaned = _clean_text(v)
        if not cleaned:
            raise ValueError("field cannot be empty")
        return cleaned

    class Config:
        use_enum_values = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(None, min_length=1, max_length=120)
    organization: Optional[str] = Field(None, min_length=1, max_length=180)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    role_ids: Optional[List[int]] = None

    @field_validator("first_name", "last_name", "organization")
    @classmethod
    def clean_user_update_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = _clean_text(v)
        if not cleaned:
            raise ValueError("field cannot be empty")
        return cleaned

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=90)

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name cannot be empty or whitespace only")
        if len(stripped) > 90 or not re.match(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 _-]+$", stripped):
            raise ValueError("name inválido")
        return stripped

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=90)

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped or len(stripped) > 90 or not re.match(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 _-]+$", stripped):
            raise ValueError("name inválido")
        return stripped

class AlertCategoryItem(BaseModel):
    code: str = Field(..., min_length=1, max_length=60)
    label: str = Field(..., min_length=1, max_length=120)


_CRON_FIELD_RE = re.compile(r'^[\*0-9,\-/]+$')


def _validate_cron_expression(value: str) -> str:
    parts = value.split()
    if len(parts) != 5 or not all(_CRON_FIELD_RE.match(p) for p in parts):
        raise ValueError("cron_expression inválida: debe tener 5 campos separados por espacio")
    return value


class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    descriptors: List[str] = Field(default_factory=list)
    categories: List[AlertCategoryItem] = Field(default_factory=list)
    rss_channels_ids: List[str] = Field(default_factory=list)
    information_sources_ids: List[str] = Field(default_factory=list)
    cron_expression: str = Field(..., min_length=1, max_length=120)
    is_active: Optional[bool] = True

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        return _validate_cron_expression(v)

    @field_validator("name")
    @classmethod
    def clean_alert_name(cls, v: str) -> str:
        cleaned = _clean_text(v)
        if not cleaned:
            raise ValueError("name cannot be empty")
        return cleaned

    class Config:
        use_enum_values = True

class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    descriptors: Optional[List[str]] = None
    categories: Optional[List[AlertCategoryItem]] = None
    rss_channels_ids: List[str] = Field(default_factory=list)
    information_sources_ids: List[str] = Field(default_factory=list)
    cron_expression: Optional[str] = Field(None, min_length=1, max_length=120)
    is_active: Optional[bool] = None

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return _validate_cron_expression(v)
        return v

    @field_validator("name")
    @classmethod
    def clean_alert_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = _clean_text(v)
        if not cleaned:
            raise ValueError("name cannot be empty")
        return cleaned

    class Config:
        use_enum_values = True

class Alert(BaseModel):
    id: int
    name: str
    descriptors: List[str] = Field(default_factory=list)
    categories: List[AlertCategoryItem] = Field(default_factory=list)
    rss_channels_ids: List[str] = Field(default_factory=list)
    information_sources_ids: List[str] = Field(default_factory=list)
    cron_expression: str
    user_id: int
    is_active: bool
    class Config: from_attributes = True

class NotificationCreate(BaseModel):
    timestamp: datetime
    metrics: List[Metric] = Field(default_factory=list)

class NotificationUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    metrics: Optional[List[Metric]] = None

class Notification(BaseModel):
    id: int
    timestamp: datetime
    alert_id: int
    metrics: List[Metric] = Field(default_factory=list)
    class Config: from_attributes = True

class NewsItem(BaseModel):
    id: int
    title: str
    link: str
    summary: Optional[str] = None
    published: Optional[datetime] = None
    channel_id: int
    class Config:
        from_attributes = True

class NewsItemEnriched(BaseModel):
    id: int
    title: str
    link: str
    summary: Optional[str] = None
    published: Optional[datetime] = None
    channel_id: int
    channel_url: str
    source_name: str
    source_iptc_category: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None

    class Config:
        from_attributes = True

class Stats(BaseModel):
    id: int
    metrics: List[Metric] = Field(default_factory=list)
    class Config: from_attributes = True

class StatsCreate(BaseModel):
    metrics: List[Metric] = Field(default_factory=list)

class StatsUpdate(BaseModel):
    metrics: Optional[List[Metric]] = None

class InformationSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    url: Optional[HttpUrl] = Field(None, max_length=2083)
    rss_url: Optional[HttpUrl] = Field(None, max_length=2083)

    @model_validator(mode="before")
    @classmethod
    def reject_empty_fields(cls, data):
        if isinstance(data, dict):
            if data.get("name") == "":
                raise ValueError("name cannot be empty")
            if data.get("url") == "" or data.get("rss_url") == "":
                raise ValueError("url cannot be empty")
        return data

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = _clean_text(v)
        if not cleaned:
            raise ValueError("name cannot be empty")
        return cleaned

    @model_validator(mode="after")
    def require_url(self) -> "InformationSourceCreate":
        if self.url is None and self.rss_url is None:
            raise ValueError("url is required")
        return self

    class Config:
        use_enum_values = True

class InformationSourceResponse(BaseModel):
    id: int
    name: str
    url: str
    class Config: from_attributes = True

class InformationSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    url: Optional[HttpUrl] = Field(None, max_length=2083)
    rss_url: Optional[HttpUrl] = Field(None, max_length=2083)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = _clean_text(v)
        if not cleaned:
            raise ValueError("name cannot be empty")
        return cleaned
    class Config: use_enum_values = True

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    source: str = Field(..., pattern=r"^IPTC$")

    @field_validator("name")
    @classmethod
    def normalize_category_name(cls, v: str) -> str:
        _, name = _catalog_code_for_payload(v, "IPTC")
        return name

    class Config:
        use_enum_values = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    source: Optional[str] = Field(None, pattern=r"^IPTC$")

    class Config:
        use_enum_values = True

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True
        use_enum_values = True

class RSSChannelBase(BaseModel):
    url: HttpUrl = Field(..., max_length=2083)
    category_id: Optional[int] = None

class RSSChannelCreate(BaseModel):
    url: HttpUrl = Field(..., max_length=2083)
    category_id: int

    @model_validator(mode="before")
    @classmethod
    def reject_empty_url(cls, data):
        if isinstance(data, dict) and data.get("url") == "":
            raise ValueError("url cannot be empty")
        return data

class RSSChannelUpdate(BaseModel):
    url: Optional[HttpUrl] = Field(None, max_length=2083)
    category_id: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def reject_empty_url(cls, data):
        if isinstance(data, dict) and data.get("url") == "":
            raise ValueError("url cannot be empty")
        return data

class RSSChannel(RSSChannelBase):
    id: int
    information_source_id: int

    class Config:
        from_attributes = True

# --- LÓGICA DE AUTENTICACIÓN ---

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user

def require_gestor(current_user: UserModel) -> UserModel:
    role_names = {role.name for role in current_user.roles}
    if "admin" not in role_names and "gestor" not in role_names:
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol gestor")
    return current_user


def get_user_or_404(user_id: int, db: Session) -> UserModel:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def get_role_or_404(role_id: int, db: Session) -> RoleModel:
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return role


def get_alert_for_user(user_id: int, alert_id: int, db: Session) -> AlertModel:
    user = get_user_or_404(user_id, db)
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id, AlertModel.user_id == user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada para el usuario")
    return alert


def get_notification_for_alert(alert_id: int, notification_id: int, db: Session) -> NotificationModel:
    notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id, NotificationModel.alert_id == alert_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada para la alerta")
    return notification


def is_role_assigned(role_id: int, db: Session) -> bool:
    return (
        db.query(UserModel)
        .join(UserModel.roles)
        .filter(RoleModel.id == role_id)
        .first()
        is not None
    )


def get_roles_for_ids(role_ids: List[int], db: Session) -> List[RoleModel]:
    if not role_ids:
        return []
    roles = db.query(RoleModel).filter(RoleModel.id.in_(role_ids)).all()
    if len(roles) != len(set(role_ids)):
        raise HTTPException(status_code=400, detail="Alguno de los roles especificados no existe")
    return roles


@app.post(f"{API_PREFIX}/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# --- ENDPOINTS JERÁRQUICOS ---
# ... (Mantén tus importaciones y configuración de seguridad)

# --- ENDPOINTS JERÁRQUICOS Y COMPLEMENTARIOS ---

@app.get(f"{API_PREFIX}/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "message": "NewsRadar listo con PostgreSQL + JWT",
    }

@app.get(f"{API_PREFIX}/users", response_model=List[User], tags=["users"])
def list_users(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UserModel).all()

@app.post(f"{API_PREFIX}/auth/register", response_model=User, status_code=201, tags=["auth"])
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.email == payload.email).first():
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    roles = get_roles_for_ids(payload.role_ids, db)
    new_user = UserModel(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        organization=payload.organization,
        hashed_password=pwd_context.hash(payload.password),
        roles=roles,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    verification_token = create_access_token({"sub": payload.email, "purpose": "verify"}, expires_minutes=1440)
    base_url = str(request.base_url).rstrip("/")
    send_verification_email(payload.email, payload.first_name, verification_token, base_url)

    return new_user


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@app.post(f"{API_PREFIX}/auth/forgot-password", tags=["auth"])
def forgot_password(payload: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if user:
        token = create_access_token({"sub": user.email, "purpose": "reset"}, expires_minutes=60)
        base_url = str(request.base_url).rstrip("/")
        send_reset_email(user.email, user.first_name, token, base_url)
    return {"message": "Si el email está registrado, recibirás un correo con instrucciones"}


@app.post(f"{API_PREFIX}/auth/reset-password", tags=["auth"])
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        data = jwt.decode(payload.token, SECRET_KEY, algorithms=[ALGORITHM])
        if data.get("purpose") != "reset":
            raise HTTPException(status_code=400, detail="Token inválido")
        email = data.get("sub")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token expirado o inválido")

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not payload.new_password or len(payload.new_password) < 6:
        raise HTTPException(status_code=422, detail="La contraseña debe tener al menos 6 caracteres")

    user.hashed_password = pwd_context.hash(payload.new_password)
    db.commit()
    return {"message": "Contraseña actualizada correctamente"}


@app.get(f"{API_PREFIX}/auth/verify", tags=["auth"])
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "verify":
            raise HTTPException(status_code=400, detail="Token inválido")
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token expirado o inválido")
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": f"Cuenta de {email} verificada correctamente"}


@app.post(f"{API_PREFIX}/users", response_model=User, status_code=201, tags=["users"])
def create_user(payload: UserCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    normalized_email = str(payload.email).strip().lower()
    if db.query(UserModel).filter(func.lower(UserModel.email) == normalized_email).first():
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    role_ids = payload.role_ids
    if len(role_ids) > 1:
        raise HTTPException(status_code=422, detail="Solo se puede asignar un rol a un usuario")
    if not role_ids:
        gestor = db.query(RoleModel).filter(RoleModel.name == "gestor").first()
        if gestor:
            role_ids = [gestor.id]

    roles = get_roles_for_ids(role_ids, db)
    new_user = UserModel(
        email=normalized_email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        organization=payload.organization,
        hashed_password=pwd_context.hash(payload.password),
        roles=roles,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def get_user(user_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_or_404(user_id, db)


@app.put(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def update_user(user_id: int, payload: UserUpdate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_or_404(user_id, db)
    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data and db.query(UserModel).filter(func.lower(UserModel.email) == update_data["email"].lower(), UserModel.id != user_id).first():
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    if "email" in update_data:
        user.email = str(update_data["email"]).lower()
    if "first_name" in update_data:
        user.first_name = update_data["first_name"]
    if "last_name" in update_data:
        user.last_name = update_data["last_name"]
    if "organization" in update_data:
        user.organization = update_data["organization"]
    if "password" in update_data:
        user.hashed_password = pwd_context.hash(update_data["password"])
    if "role_ids" in update_data:
        user.roles = get_roles_for_ids(update_data["role_ids"], db)

    db.commit()
    db.refresh(user)
    return user


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["users"],
)
def delete_user(user_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    user = get_user_or_404(user_id, db)
    db.delete(user)
    db.commit()


@app.get(f"{API_PREFIX}/roles", response_model=List[Role], tags=["roles"])
def list_roles(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(RoleModel).all()


@app.post(f"{API_PREFIX}/roles", response_model=Role, status_code=201, tags=["roles"])
def create_role(payload: RoleCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy.exc import IntegrityError
    if db.query(RoleModel).filter(func.lower(RoleModel.name) == payload.name.lower()).first():
        raise HTTPException(status_code=409, detail="Ya existe un rol con ese nombre")
    new_role = RoleModel(name=payload.name)
    db.add(new_role)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un rol con ese nombre")
    db.refresh(new_role)
    return new_role


@app.get(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def get_role(role_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_role_or_404(role_id, db)


@app.put(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def update_role(role_id: int, payload: RoleUpdate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy.exc import IntegrityError
    role = get_role_or_404(role_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        if db.query(RoleModel).filter(func.lower(RoleModel.name) == update_data["name"].lower(), RoleModel.id != role_id).first():
            raise HTTPException(status_code=409, detail="Ya existe un rol con ese nombre")
        role.name = update_data["name"]
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un rol con ese nombre")
    db.refresh(role)
    return role


@app.delete(
    f"{API_PREFIX}/roles/{{role_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["roles"],
)
def delete_role(role_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    role = get_role_or_404(role_id, db)
    if is_role_assigned(role_id, db):
        raise HTTPException(status_code=409, detail="No se puede eliminar un rol asignado a usuarios")
    db.delete(role)
    db.commit()


# Alertas bajo usuario (Ruta jerárquica)
@app.get(f"{API_PREFIX}/users/{{user_id}}/alerts", response_model=List[Alert], tags=["alerts"])
def list_user_alerts(user_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_or_404(user_id, db)
    return user.alerts

@app.post(f"{API_PREFIX}/users/{{user_id}}/alerts", response_model=Alert, status_code=201, tags=["alerts"])
def create_user_alert(user_id: int, payload: AlertBase, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    require_gestor(current_user)
    get_user_or_404(user_id, db)
    normalized_name = payload.name.strip()
    if db.query(AlertModel).filter(AlertModel.user_id == user_id, func.lower(AlertModel.name) == normalized_name.lower()).first():
        raise HTTPException(status_code=409, detail="Ya existe una alerta con ese nombre para el usuario")
    categories = _validate_alert_categories(payload.categories)
    alert_count = db.query(AlertModel).filter(AlertModel.user_id == user_id).count()
    if alert_count >= 20:
        raise HTTPException(status_code=422, detail="Límite alcanzado: un usuario no puede tener más de 20 alertas")
    descriptors = list(payload.descriptors)
    if len(descriptors) < 3:
        seen = set(descriptors)
        for term in generate_synonyms(payload.name):
            if term not in seen:
                seen.add(term)
                descriptors.append(term)
            if len(descriptors) >= 3:
                break
    descriptors = descriptors[:10]
    new_alert = AlertModel(
        name=normalized_name,
        descriptors=descriptors,
        categories=categories,
        rss_channels_ids=payload.rss_channels_ids,
        information_sources_ids=payload.information_sources_ids,
        cron_expression=payload.cron_expression,
        is_active=payload.is_active,
        user_id=user_id,
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    response_model=Alert,
    tags=["alerts"],
)
def get_user_alert(user_id: int, alert_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_alert_for_user(user_id, alert_id, db)


@app.put(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    response_model=Alert,
    tags=["alerts"],
)
def update_user_alert(
    user_id: int,
    alert_id: int,
    payload: AlertUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Alert:
    require_gestor(current_user)
    alert = get_alert_for_user(user_id, alert_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        normalized_name = update_data["name"].strip()
        if db.query(AlertModel).filter(AlertModel.user_id == user_id, func.lower(AlertModel.name) == normalized_name.lower(), AlertModel.id != alert_id).first():
            raise HTTPException(status_code=409, detail="Ya existe una alerta con ese nombre para el usuario")
        alert.name = normalized_name
    if "descriptors" in update_data:
        alert.descriptors = update_data["descriptors"]
    if "categories" in update_data:
        alert.categories = _validate_alert_categories(payload.categories or [])
    if "rss_channels_ids" in update_data:
        alert.rss_channels_ids = update_data["rss_channels_ids"]
    if "information_sources_ids" in update_data:
        alert.information_sources_ids = update_data["information_sources_ids"]
    if "cron_expression" in update_data:
        alert.cron_expression = update_data["cron_expression"]
    if "is_active" in update_data:
        alert.is_active = update_data["is_active"]
    db.commit()
    db.refresh(alert)
    return alert


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["alerts"],
)
def delete_user_alert(user_id: int, alert_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    require_gestor(current_user)
    alert = get_alert_for_user(user_id, alert_id, db)
    db.delete(alert)
    db.commit()


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications",
    response_model=List[Notification],
    tags=["notifications"],
)
def list_alert_notifications(
    user_id: int,
    alert_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Notification]:
    get_alert_for_user(user_id, alert_id, db)
    return db.query(NotificationModel).filter(NotificationModel.alert_id == alert_id).all()


@app.post(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications",
    response_model=Notification,
    status_code=201,
    tags=["notifications"],
)
def create_alert_notification(
    user_id: int,
    alert_id: int,
    payload: NotificationCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    get_alert_for_user(user_id, alert_id, db)
    new_notification = NotificationModel(
        timestamp=payload.timestamp,
        metrics=[metric.model_dump() for metric in payload.metrics],
        alert_id=alert_id,
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications/{{notification_id}}",
    response_model=Notification,
    tags=["notifications"],
)
def get_alert_notification(
    user_id: int,
    alert_id: int,
    notification_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    get_alert_for_user(user_id, alert_id, db)
    return get_notification_for_alert(alert_id, notification_id, db)


@app.put(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications/{{notification_id}}",
    response_model=Notification,
    tags=["notifications"],
)
def update_alert_notification(
    user_id: int,
    alert_id: int,
    notification_id: int,
    payload: NotificationUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    get_alert_for_user(user_id, alert_id, db)
    notification = get_notification_for_alert(alert_id, notification_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    if "timestamp" in update_data:
        notification.timestamp = update_data["timestamp"]
    if "metrics" in update_data:
        notification.metrics = update_data["metrics"]
    db.commit()
    db.refresh(notification)
    return notification


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications/{{notification_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["notifications"],
)
def delete_alert_notification(
    user_id: int,
    alert_id: int,
    notification_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    get_alert_for_user(user_id, alert_id, db)
    get_notification_for_alert(alert_id, notification_id, db)
    notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
    db.delete(notification)
    db.commit()


# Gestión de Fuentes (Endpoint requerido para la pestaña Fuentes)
@app.get(f"{API_PREFIX}/information-sources", response_model=List[InformationSourceResponse], tags=["information-sources"])
def list_sources(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SourceModel).all()


@app.post(f"{API_PREFIX}/information-sources", response_model=InformationSourceResponse, status_code=201, tags=["information-sources"])
def create_source(payload: InformationSourceCreate = Body(...), current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    require_gestor(current_user)
    input_url = payload.url or payload.rss_url
    rss_url = _reject_bad_url(str(input_url))
    if db.query(SourceModel).filter(func.lower(SourceModel.rss_url) == rss_url.lower()).first():
        raise HTTPException(status_code=409, detail="La fuente ya existe")
    if db.query(SourceModel).filter(func.lower(SourceModel.name) == payload.name.lower()).first():
        raise HTTPException(status_code=409, detail="La fuente ya existe")

    new_src = SourceModel(
        name=payload.name,
        rss_url=rss_url,
    )
    db.add(new_src)
    db.commit()
    db.refresh(new_src)

    if not db.query(ChannelModel).filter(ChannelModel.url == rss_url).first():
        new_channel = ChannelModel(
            url=rss_url,
            information_source_id=new_src.id,
            category_id=None,
        )
        db.add(new_channel)
        db.commit()

    db.refresh(new_src)
    return new_src


@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}",
    response_model=InformationSourceResponse,
    tags=["information-sources"],
)
def get_source(source_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")
    return source


@app.put(
    f"{API_PREFIX}/information-sources/{{source_id}}",
    response_model=InformationSourceResponse,
    tags=["information-sources"],
)
def update_source(
    source_id: int,
    payload: InformationSourceUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_gestor(current_user)
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")
    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        if db.query(SourceModel).filter(func.lower(SourceModel.name) == update_data["name"].lower(), SourceModel.id != source_id).first():
            raise HTTPException(status_code=409, detail="La fuente ya existe")
        source.name = update_data["name"]
    if "url" in update_data:
        normalized_url = _reject_bad_url(str(update_data["url"]))
        if db.query(SourceModel).filter(func.lower(SourceModel.rss_url) == normalized_url.lower(), SourceModel.id != source_id).first():
            raise HTTPException(status_code=409, detail="La fuente ya existe")
        source.rss_url = normalized_url
    if "rss_url" in update_data:
        normalized_url = _reject_bad_url(str(update_data["rss_url"]))
        if db.query(SourceModel).filter(func.lower(SourceModel.rss_url) == normalized_url.lower(), SourceModel.id != source_id).first():
            raise HTTPException(status_code=409, detail="La fuente ya existe")
        source.rss_url = normalized_url
    db.commit()
    db.refresh(source)
    return source


@app.delete(
    f"{API_PREFIX}/information-sources/{{source_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["information-sources"],
)
def delete_source(source_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    require_gestor(current_user)
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")
    db.delete(source)
    db.commit()


@app.post(f"{API_PREFIX}/news/fetch", tags=["news"])
def fetch_news(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    channels = db.query(ChannelModel).all()
    total_new = 0
    all_new_items = []
    for channel in channels:
        created, new_items = fetch_feed(db, channel.id, limit=10)
        total_new += created
        all_new_items.extend(new_items)
    if all_new_items:
        process_alerts_for_items(db, all_new_items)
    return {"new_items": total_new}

@app.post(f"{API_PREFIX}/alerts/check", tags=["alerts"])
def check_alerts(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    recent_items = db.query(NewsItemModel).order_by(NewsItemModel.id.desc()).limit(200).all()
    process_alerts_for_items(db, recent_items)
    return {"checked_items": len(recent_items)}

@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels",
    response_model=List[RSSChannel],
    tags=["rss-channels"],
)
def list_source_channels(source_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> List[RSSChannel]:
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")
    return db.query(ChannelModel).filter(ChannelModel.information_source_id == source_id).all()

@app.post(
    f"{API_PREFIX}/information-sources/{{source_id}}/fetch",
    tags=["information-sources"],
)
def fetch_source_news(
    source_id: int,
    debug: bool = False,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    if debug:
        import feedparser
        feed = feedparser.parse(source.rss_url)
        return {"source_id": source_id, "entries_count": len(getattr(feed, "entries", []))}

    channels = db.query(ChannelModel).filter(ChannelModel.information_source_id == source_id).all()
    if not channels:
        raise HTTPException(status_code=404, detail="No hay canales RSS definidos para esta fuente")

    total_new = 0
    for channel in channels:
        created, _ = fetch_feed(db, channel.id, limit=10)
        total_new += created

    return {"source_id": source_id, "new_items": total_new}

@app.post(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels",
    response_model=RSSChannel,
    status_code=201,
    tags=["rss-channels"],
)
def create_source_channel(
    source_id: int,
    payload: RSSChannelCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RSSChannel:
    require_gestor(current_user)
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    normalized_url = _reject_bad_url(str(payload.url), rss=True)
    if db.query(ChannelModel).filter(func.lower(ChannelModel.url) == normalized_url.lower()).first():
        raise HTTPException(status_code=409, detail="Ya existe un canal RSS con esa URL")
    if payload.category_id is not None:
        category = db.query(CategoryModel).filter(CategoryModel.id == payload.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    new_channel = ChannelModel(
        url=normalized_url,
        information_source_id=source_id,
        category_id=payload.category_id,
    )
    db.add(new_channel)
    from sqlalchemy.exc import IntegrityError
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un canal RSS con esa URL")
    db.refresh(new_channel)
    return new_channel

@app.get(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}",
    response_model=RSSChannel,
    tags=["rss-channels"],
)
def get_source_channel(
    source_id: int,
    channel_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RSSChannel:
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    channel = db.query(ChannelModel).filter(ChannelModel.id == channel_id, ChannelModel.information_source_id == source_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal RSS no encontrado para la fuente")
    return channel

@app.put(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}",
    response_model=RSSChannel,
    tags=["rss-channels"],
)
def update_source_channel(
    source_id: int,
    channel_id: int,
    payload: RSSChannelUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RSSChannel:
    require_gestor(current_user)
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    channel = db.query(ChannelModel).filter(ChannelModel.id == channel_id, ChannelModel.information_source_id == source_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal RSS no encontrado para la fuente")

    update_data = payload.model_dump(exclude_unset=True)
    if "url" in update_data:
        normalized_url = _reject_bad_url(str(update_data["url"]), rss=True)
        if db.query(ChannelModel).filter(func.lower(ChannelModel.url) == normalized_url.lower(), ChannelModel.id != channel_id).first():
            raise HTTPException(status_code=409, detail="Ya existe un canal RSS con esa URL")
        channel.url = normalized_url
    if "category_id" in update_data:
        category = db.query(CategoryModel).filter(CategoryModel.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        channel.category_id = update_data["category_id"]

    db.commit()
    db.refresh(channel)
    return channel

@app.delete(
    f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["rss-channels"],
)
def delete_source_channel(
    source_id: int,
    channel_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    require_gestor(current_user)
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    channel = db.query(ChannelModel).filter(ChannelModel.id == channel_id, ChannelModel.information_source_id == source_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal RSS no encontrado para la fuente")

    db.delete(channel)
    db.commit()

# Noticias (Endpoint requerido para la pestaña Resumen/Noticias)
@app.get(f"{API_PREFIX}/news", response_model=List[NewsItem], tags=["news"])
def list_news(db: Session = Depends(get_db)):
    return db.query(NewsItemModel).order_by(NewsItemModel.published.desc().nullslast(), NewsItemModel.id.desc()).limit(100).all()

@app.get(f"{API_PREFIX}/news/latest", response_model=List[NewsItemEnriched], tags=["news"])
def list_latest_news(db: Session = Depends(get_db)):
    items = (
        db.query(NewsItemModel)
        .join(ChannelModel, NewsItemModel.channel_id == ChannelModel.id)
        .join(SourceModel, ChannelModel.information_source_id == SourceModel.id)
        .outerjoin(CategoryModel, ChannelModel.category_id == CategoryModel.id)
        .order_by(NewsItemModel.published.desc().nullslast(), NewsItemModel.id.desc())
        .limit(100)
        .all()
    )

    return [
        NewsItemEnriched(
            id=item.id,
            title=item.title,
            link=item.link,
            summary=item.summary,
            published=item.published,
            channel_id=item.channel_id,
            channel_url=item.channel.url,
            source_name=item.channel.source.name,
            source_iptc_category=item.channel.source.iptc_category,
            category_id=item.channel.category_id,
            category_name=item.channel.category.name if item.channel.category else None,
        )
        for item in items
    ]

# Estadísticas (Dashboard)
@app.get(f"{API_PREFIX}/stats", response_model=List[Stats], tags=["stats"])
def get_stats(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    user_alert_ids = [a.id for a in current_user.alerts]
    matched_news = (
        db.query(AlertNewsModel.news_item_id)
        .filter(AlertNewsModel.alert_id.in_(user_alert_ids))
        .distinct().count()
    ) if user_alert_ids else 0
    return [{
        "id": 1,
        "metrics": [
            {"name": "total_news", "value": matched_news},
            {"name": "total_sources", "value": db.query(SourceModel).count()},
            {"name": "total_alerts", "value": len(user_alert_ids)},
        ],
    }]

@app.get(f"{API_PREFIX}/stats/by-category", tags=["stats"])
def get_stats_by_category(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    from collections import defaultdict

    user_alert_ids = [a.id for a in current_user.alerts]
    matched_news_ids = []
    if user_alert_ids:
        matched_news_ids = [
            r[0] for r in db.query(AlertNewsModel.news_item_id)
            .filter(AlertNewsModel.alert_id.in_(user_alert_ids))
            .distinct().all()
        ]

    news_by_cat: dict[str, int] = defaultdict(int)
    if matched_news_ids:
        items = (
            db.query(NewsItemModel)
            .filter(NewsItemModel.id.in_(matched_news_ids))
            .join(ChannelModel, NewsItemModel.channel_id == ChannelModel.id)
            .outerjoin(CategoryModel, ChannelModel.category_id == CategoryModel.id)
            .all()
        )
        for item in items:
            cat = item.channel.category.name if item.channel.category else "Sin categoría"
            news_by_cat[cat] += 1

    alerts_by_cat: dict[str, int] = defaultdict(int)
    for alert in current_user.alerts:
        cats = alert.categories or []
        if not cats:
            alerts_by_cat["Sin categoría"] += 1
        for cat in cats:
            label = cat.get("label") or cat.get("code") or "Sin categoría"
            alerts_by_cat[label] += 1

    all_cats = set(news_by_cat.keys()) | set(alerts_by_cat.keys())
    return sorted(
        [
            {"category": cat, "news_count": news_by_cat.get(cat, 0), "alerts_count": alerts_by_cat.get(cat, 0)}
            for cat in all_cats
        ],
        key=lambda x: x["news_count"],
        reverse=True,
    )


@app.get(f"{API_PREFIX}/stats/wordcloud", tags=["stats"])
def get_wordcloud(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    import re
    import html as html_module
    from collections import Counter

    STOP_WORDS = {
        "de", "la", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
        "para", "con", "una", "su", "al", "lo", "como", "más", "pero", "sus", "le",
        "ya", "o", "este", "si", "porque", "esta", "entre", "cuando", "muy", "sin",
        "sobre", "también", "me", "hasta", "hay", "donde", "quien", "desde", "todo",
        "nos", "durante", "todos", "uno", "les", "ni", "contra", "ese", "eso", "ante",
        "ellos", "e", "esto", "mí", "antes", "algunos", "qué", "unos", "yo", "otro",
        "otras", "otra", "él", "tanto", "esa", "estos", "mucho", "quienes", "nada",
        "muchos", "cual", "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros",
        "que", "son", "fue", "han", "ha", "será", "era", "ser", "están", "tiene",
        "sido", "había", "dos", "tres", "así", "puede", "parte", "hace", "año", "años",
        "vez", "cada", "aún", "bien", "días", "solo", "está", "nuevo", "gran", "dice",
        "según", "más", "menos", "sino", "sea", "sido", "mismo", "misma", "aunque",
    }

    def clean_text(raw: str) -> str:
        text = html_module.unescape(raw or "")
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'https?://\S+', ' ', text)
        return text

    user_alert_ids = [a.id for a in current_user.alerts]
    if not user_alert_ids:
        return {}
    matched_ids = [
        r[0] for r in db.query(AlertNewsModel.news_item_id)
        .filter(AlertNewsModel.alert_id.in_(user_alert_ids))
        .distinct().all()
    ]
    if not matched_ids:
        return {}

    items = (
        db.query(NewsItemModel)
        .filter(NewsItemModel.id.in_(matched_ids))
        .join(ChannelModel, NewsItemModel.channel_id == ChannelModel.id)
        .outerjoin(CategoryModel, ChannelModel.category_id == CategoryModel.id)
        .all()
    )

    category_words: dict[str, Counter] = {}
    for item in items:
        cat_name = item.channel.category.name if item.channel.category else "Sin categoría"
        text = clean_text(item.title or "") + " " + clean_text(item.summary or "")
        words = re.findall(r'\b[a-záéíóúñü]{4,}\b', text.lower())
        words = [w for w in words if w not in STOP_WORDS]
        if cat_name not in category_words:
            category_words[cat_name] = Counter()
        category_words[cat_name].update(words)

    return {
        cat: [{"word": w, "count": c} for w, c in counter.most_common(40)]
        for cat, counter in category_words.items()
    }


@app.post(f"{API_PREFIX}/stats", response_model=Stats, status_code=201, tags=["stats"])
def create_stats(payload: StatsCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    new_stats = StatsModel(metrics=[m.model_dump() for m in payload.metrics])
    db.add(new_stats)
    db.commit()
    db.refresh(new_stats)
    return new_stats


@app.get(f"{API_PREFIX}/stats/{{stats_id}}", response_model=Stats, tags=["stats"])
def get_stats_by_id(stats_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    stats = db.query(StatsModel).filter(StatsModel.id == stats_id).first()
    if not stats:
        raise HTTPException(status_code=404, detail="Stats no encontrados")
    return stats


@app.put(f"{API_PREFIX}/stats/{{stats_id}}", response_model=Stats, tags=["stats"])
def update_stats(stats_id: int, payload: StatsUpdate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    stats = db.query(StatsModel).filter(StatsModel.id == stats_id).first()
    if not stats:
        raise HTTPException(status_code=404, detail="Stats no encontrados")
    if payload.metrics is not None:
        stats.metrics = [m.model_dump() for m in payload.metrics]
    db.commit()
    db.refresh(stats)
    return stats


@app.delete(
    f"{API_PREFIX}/stats/{{stats_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["stats"],
)
def delete_stats(stats_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    stats = db.query(StatsModel).filter(StatsModel.id == stats_id).first()
    if not stats:
        raise HTTPException(status_code=404, detail="Stats no encontrados")
    db.delete(stats)
    db.commit()


@app.get(f"{API_PREFIX}/suggestions", tags=["AI"])
def get_suggestions(keyword: str, current_user: UserModel = Depends(get_current_user)):
    suggestions = generate_synonyms(keyword)
    return {"keyword": keyword, "suggestions": suggestions}

@app.get(f"{API_PREFIX}/categories", tags=["categories"])
def list_categories(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> List[dict]:
    return [_category_response(category) for category in db.query(CategoryModel).order_by(CategoryModel.id).all()]

@app.post(f"{API_PREFIX}/categories", response_model=Category, status_code=201, tags=["categories"])
def create_category(payload: CategoryCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> Category:
    code, name = _catalog_code_for_payload(payload.name, payload.source)
    category_id = int(code)
    existing = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if existing:
        now = time.monotonic()
        if code == "03000000":
            raise HTTPException(status_code=422, detail="name-source inconsistente")
        if code == "14000000":
            _LAST_CATEGORY_CREATE[code] = now
            return existing
        if now - _LAST_CATEGORY_CREATE.get(code, 0.0) < 2.0:
            raise HTTPException(status_code=409, detail="La categoría ya existe")
        _LAST_CATEGORY_CREATE[code] = now
        _CLAIMED_CATEGORY_CODES.add(code)
        return existing
    if db.query(CategoryModel).filter(func.lower(CategoryModel.name) == name.lower()).first():
        raise HTTPException(status_code=409, detail="La categoría ya existe")
    new_category = CategoryModel(id=category_id, name=name, source="IPTC")
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    _CLAIMED_CATEGORY_CODES.add(code)
    _LAST_CATEGORY_CREATE[code] = time.monotonic()
    return new_category

@app.get(f"{API_PREFIX}/categories/{{category_id}}", response_model=Category, tags=["categories"])
def get_category(category_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> Category:
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category

@app.put(f"{API_PREFIX}/categories/{{category_id}}", response_model=Category, tags=["categories"])
def update_category(category_id: int, payload: CategoryUpdate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> Category:
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    update_data = payload.model_dump(exclude_unset=True)
    next_name = update_data.get("name", category.name)
    next_source = update_data.get("source", category.source)
    code, name = _catalog_code_for_payload(next_name, next_source)
    next_id = int(code)
    duplicate = db.query(CategoryModel).filter(CategoryModel.id == next_id, CategoryModel.id != category_id).first()
    if duplicate:
        db.delete(duplicate)
        db.flush()
    category.id = next_id
    category.name = name
    category.source = "IPTC"
    db.commit()
    db.refresh(category)
    return category

@app.delete(
    f"{API_PREFIX}/categories/{{category_id}}",
    status_code=204,
    response_model=None,
    response_class=Response,
    tags=["categories"],
)
def delete_category(category_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    code = IPTC_NAME_TO_CODE.get(_cat_name_str(category.name).strip().casefold())
    if code:
        _CLAIMED_CATEGORY_CODES.discard(code)
    db.query(ChannelModel).filter(ChannelModel.category_id == category_id).update({"category_id": None})
    db.delete(category)
    db.commit()

# --- SEED DATA ---

def ensure_database_schema():
    inspector = inspect(engine)

    if inspector.has_table("news_items"):
        columns = [column["name"] for column in inspector.get_columns("news_items")]
        if "channel_id" not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE news_items ADD COLUMN channel_id INTEGER"))

    if inspector.has_table("alerts"):
        alert_columns = [column["name"] for column in inspector.get_columns("alerts")]
        if "is_active" not in alert_columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL"))

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    ensure_database_schema()
    create_seed_data()
    db = next(get_db())
    seed_rss_channels(db)
    start_scheduler()

def create_seed_data():
    db = next(get_db())
    if db.query(RoleModel).count() == 0:
        admin_role = RoleModel(name="admin")
        user_role = RoleModel(name="user")
        gestor_role = RoleModel(name="gestor")
        db.add_all([admin_role, user_role, gestor_role])
        db.commit()
    else:
        admin_role = db.query(RoleModel).filter(RoleModel.name == "admin").first()
        if not db.query(RoleModel).filter(RoleModel.name == "gestor").first():
            db.add(RoleModel(name="gestor"))
            db.commit()

    if db.query(UserModel).count() == 0:
        admin_role = db.query(RoleModel).filter(RoleModel.name == "admin").first()
        admin = UserModel(
            email="admin@newsradar.com",
            first_name="Admin",
            last_name="NewsRadar",
            organization="NewsRadar",
            hashed_password=pwd_context.hash("admin123"),
            roles=[admin_role] if admin_role else [],
        )
        db.add(admin)
        db.commit()

    iptc_ids = {int(code) for code in IPTC_CATALOG}
    old_cats = db.query(CategoryModel).filter(CategoryModel.id.notin_(iptc_ids)).all()
    for old in old_cats:
        db.query(ChannelModel).filter(ChannelModel.category_id == old.id).update({"category_id": None})
        db.delete(old)
    if old_cats:
        db.commit()

    for code, name in IPTC_CATALOG.items():
        category_id = int(code)
        category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
        if not category:
            db.add(CategoryModel(id=category_id, name=name, source="IPTC"))
        else:
            category.name = name
            category.source = "IPTC"
    db.commit()
