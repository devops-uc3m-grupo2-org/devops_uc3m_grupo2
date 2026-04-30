from __future__ import annotations
import os
import pathlib
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Response, Body, Request
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from dotenv import load_dotenv # Nueva importación

# --- CONFIGURACIÓN DE ENTORNO ---
load_dotenv() # Carga las variables del .env

# Importaciones de tu core y modelos refactorizados con ALIAS
from app.core.database import engine, Base, get_db
from app.models.models import (
    User as UserModel,
    Role as RoleModel,
    Alert as AlertModel,
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
from app.services.notifications import send_verification_email
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
    name: str
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
    first_name: str
    last_name: str
    organization: str
    password: str
    role_ids: List[int] = Field(default_factory=list)

    class Config:
        use_enum_values = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    password: Optional[str] = None
    role_ids: Optional[List[int]] = None

class RoleCreate(BaseModel):
    name: str

class RoleUpdate(BaseModel):
    name: Optional[str] = None

class AlertCategoryItem(BaseModel):
    code: IPTCCategoryEnum
    label: IPTCCategoryEnum

    class Config:
        use_enum_values = True

class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    descriptors: List[str] = Field(default_factory=list)
    categories: List[AlertCategoryItem] = Field(default_factory=list)
    rss_channels_ids: List[str] = Field(default_factory=list)
    information_sources_ids: List[str] = Field(default_factory=list)
    cron_expression: str = Field(..., min_length=1, max_length=120)
    is_active: Optional[bool] = True

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

class InformationSourceCreate(BaseModel):
    name: str
    medium: Optional[str] = None
    rss_url: HttpUrl
    iptc_category: Optional[IPTCCategoryEnum] = None

    class Config:
        use_enum_values = True

class CategoryBase(BaseModel):
    name: IPTCCategoryEnum
    source: str = "IPTC"

    class Config:
        use_enum_values = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[IPTCCategoryEnum] = None
    source: Optional[str] = None

    class Config:
        use_enum_values = True

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True
        use_enum_values = True

class RSSChannelBase(BaseModel):
    url: HttpUrl
    category_id: Optional[int] = None

class RSSChannelCreate(RSSChannelBase):
    pass

class RSSChannelUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    category_id: Optional[int] = None

class RSSChannel(RSSChannelBase):
    id: int
    information_source_id: int

    class Config:
        from_attributes = True

# --- LÓGICA DE AUTENTICACIÓN ---

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
    if "admin" not in role_names:
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

@app.post(f"{API_PREFIX}/auth/register", response_model=User, status_code=200, tags=["auth"])
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

    verification_token = create_access_token({"sub": payload.email, "purpose": "verify"})
    base_url = str(request.base_url).rstrip("/")
    send_verification_email(payload.email, payload.first_name, verification_token, base_url)

    return new_user


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
    return new_user


@app.get(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def get_user(user_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_or_404(user_id, db)


@app.put(f"{API_PREFIX}/users/{{user_id}}", response_model=User, tags=["users"])
def update_user(user_id: int, payload: UserUpdate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_or_404(user_id, db)
    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data and db.query(UserModel).filter(UserModel.email == update_data["email"], UserModel.id != user_id).first():
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    if "email" in update_data:
        user.email = update_data["email"]
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
    new_role = RoleModel(name=payload.name)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


@app.get(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def get_role(role_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_role_or_404(role_id, db)


@app.put(f"{API_PREFIX}/roles/{{role_id}}", response_model=Role, tags=["roles"])
def update_role(role_id: int, payload: RoleUpdate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    role = get_role_or_404(role_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        role.name = update_data["name"]
    db.commit()
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
    new_alert = AlertModel(
        name=payload.name,
        descriptors=payload.descriptors,
        categories=[cat.dict() for cat in payload.categories],
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
        alert.name = update_data["name"]
    if "descriptors" in update_data:
        alert.descriptors = update_data["descriptors"]
    if "categories" in update_data:
        alert.categories = [cat.dict() for cat in update_data["categories"]]
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
@app.get(f"{API_PREFIX}/information-sources", tags=["information-sources"])
def list_sources(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SourceModel).all()


@app.post(f"{API_PREFIX}/information-sources", status_code=201, tags=["information-sources"])
def create_source(payload: InformationSourceCreate = Body(...), current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    rss_url = str(payload.rss_url)
    # Verificamos si ya existe por la URL RSS
    if db.query(SourceModel).filter(SourceModel.rss_url == rss_url).first():
        raise HTTPException(status_code=409, detail="La fuente ya existe")

    iptc_category = payload.iptc_category
    if hasattr(iptc_category, 'value'):
        iptc_category = iptc_category.value

    new_src = SourceModel(
        name=payload.name,
        medium=payload.medium,
        rss_url=rss_url,
        iptc_category=iptc_category
    )
    db.add(new_src)
    db.commit()
    db.refresh(new_src)

    category_id = None
    if payload.iptc_category:
        category = db.query(CategoryModel).filter(CategoryModel.name == payload.iptc_category).first()
        if not category:
            category = CategoryModel(name=payload.iptc_category, source="IPTC")
            db.add(category)
            db.commit()
            db.refresh(category)
        category_id = category.id

    if not db.query(ChannelModel).filter(ChannelModel.url == rss_url).first():
        new_channel = ChannelModel(
            url=rss_url,
            information_source_id=new_src.id,
            category_id=category_id,
        )
        db.add(new_channel)
        db.commit()

    db.refresh(new_src)
    return new_src


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
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    if payload.category_id is not None:
        category = db.query(CategoryModel).filter(CategoryModel.id == payload.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    new_channel = ChannelModel(
        url=str(payload.url),
        information_source_id=source_id,
        category_id=payload.category_id,
    )
    db.add(new_channel)
    db.commit()
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
    source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente de información no encontrada")

    channel = db.query(ChannelModel).filter(ChannelModel.id == channel_id, ChannelModel.information_source_id == source_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal RSS no encontrado para la fuente")

    update_data = payload.model_dump(exclude_unset=True)
    if "url" in update_data:
        channel.url = str(update_data["url"])
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
    return [{
        "id": 1,
        "metrics": [
            {"name": "total_news", "value": db.query(NewsItemModel).count()},
            {"name": "total_sources", "value": db.query(SourceModel).count()},
            {"name": "total_alerts", "value": db.query(AlertModel).count()},
        ],
    }]

@app.get(f"{API_PREFIX}/suggestions", tags=["AI"])
def get_suggestions(keyword: str, current_user: UserModel = Depends(get_current_user)):
    suggestions = generate_synonyms(keyword)
    return {"keyword": keyword, "suggestions": suggestions}

@app.get(f"{API_PREFIX}/categories", response_model=List[Category], tags=["categories"])
def list_categories(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> List[Category]:
    return db.query(CategoryModel).all()

@app.post(f"{API_PREFIX}/categories", response_model=Category, status_code=201, tags=["categories"])
def create_category(payload: CategoryCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> Category:
    new_category = CategoryModel(name=payload.name, source=payload.source)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
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
    if "name" in update_data:
        category.name = update_data["name"]
    if "source" in update_data:
        category.source = update_data["source"]
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
    db.delete(category)
    db.commit()

# --- SEED DATA CORREGIDO (USANDO ALIAS) ---

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
    # Corregido: Usar RoleModel y UserModel en lugar de Role y User
    if db.query(RoleModel).count() == 0:
        admin_role = RoleModel(name="admin")
        user_role = RoleModel(name="user")
        db.add_all([admin_role, user_role])
        db.commit()
    else:
        admin_role = db.query(RoleModel).filter(RoleModel.name == "admin").first()
        user_role = db.query(RoleModel).filter(RoleModel.name == "user").first()

    if db.query(UserModel).count() == 0:
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
