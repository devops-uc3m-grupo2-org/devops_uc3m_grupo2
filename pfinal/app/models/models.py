import enum
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Text, DateTime, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    organization = Column(String(180), nullable=False)
    hashed_password = Column(String(128), nullable=False)
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("Role", secondary=user_roles, backref="users")

    @property
    def role_ids(self):
        return [role.id for role in self.roles]


class IPTCCategoryEnum(str, enum.Enum):
    ARTS_AND_ENTERTAINMENT = "Artes, cultura, entretenimiento y medios"
    CRIME_LAW_AND_JUSTICE = "Policía y justicia"
    DISASTERS_AND_ACCIDENTS = "Catástrofes y accidentes"
    ECONOMY_BUSINESS_AND_FINANCE = "Economía, negocios y finanzas"
    EDUCATION = "Educación"
    ENVIRONMENT = "Medio ambiente"
    HEALTH = "Salud"
    HUMAN_INTEREST = "Interés humano, animales, insólito"
    LABOUR = "Mano de obra"
    LIFESTYLE_AND_LEISURE = "Estilo de vida y tiempo libre"
    POLITICS = "Política"
    RELIGION_AND_BELIEF = "Religión y culto"
    SCIENCE_AND_TECHNOLOGY = "Ciencia y tecnología"
    SOCIETY = "Sociedad"
    SPORT = "Deporte"
    CONFLICTS_WAR_AND_PEACE = "Conflicto, guerra y paz"
    WEATHER = "Meteorología"

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    # 2. Aplicas el Enum a la columna
    name = Column(SQLEnum(IPTCCategoryEnum), nullable=False)
    source = Column(String, default="IPTC")

class InformationSource(Base):
    __tablename__ = "information_sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    medium = Column(String(120), nullable=True)
    rss_url = Column(String, nullable=False)
    iptc_category = Column(String(120), nullable=True)
    rss_channels = relationship("RSSChannel", back_populates="source", cascade="all, delete-orphan")

    @property
    def url(self):
        return self.rss_url

class RSSChannel(Base):
    __tablename__ = "rss_channels"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, unique=True)
    information_source_id = Column(Integer, ForeignKey("information_sources.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    source = relationship("InformationSource", back_populates="rss_channels")
    category = relationship("Category")
    news_items = relationship("NewsItem", back_populates="channel")

class NewsItem(Base):
    __tablename__ = "news_items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False, unique=True)
    summary = Column(Text, nullable=True)
    published = Column(DateTime, nullable=True)
    channel_id = Column(Integer, ForeignKey("rss_channels.id"))
    channel = relationship("RSSChannel", back_populates="news_items")
    matched_alerts = relationship("AlertNews", back_populates="news_item", cascade="all, delete-orphan")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    descriptors = Column(JSON, default=[])
    categories = Column(JSON, default=[])
    rss_channels_ids = Column(JSON, default=[])
    information_sources_ids = Column(JSON, default=[])
    cron_expression = Column(String(120), default="*/5 * * * *")
    is_active = Column(Boolean, default=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")
    matched_news = relationship("AlertNews", back_populates="alert", cascade="all, delete-orphan")

class AlertNews(Base):
    __tablename__ = "alert_news"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"))
    news_item_id = Column(Integer, ForeignKey("news_items.id", ondelete="CASCADE"))
    alert = relationship("Alert", back_populates="matched_news")
    news_item = relationship("NewsItem", back_populates="matched_alerts")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert_id = Column(Integer, ForeignKey("alerts.id"))
    metrics = Column(JSON, default=[])
    alert = relationship("Alert", back_populates="notifications")

class Stats(Base):
    __tablename__ = "stats"
    id = Column(Integer, primary_key=True, index=True)
    metrics = Column(JSON, default=[])