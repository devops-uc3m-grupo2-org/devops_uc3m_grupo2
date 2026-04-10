from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import json


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

    role_ids = []  # Se manejará en Fase 2 con tabla intermedia


# Models for Sprint 2: InformationSource and NewsItem
class InformationSource(Base):
    __tablename__ = "information_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    medium = Column(String, nullable=False)  # p.ej. 'RTVE', 'El País'
    rss_url = Column(String, unique=True, nullable=False)
    iptc_category = Column(String, nullable=True)  # luego mapeas a IPTC


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False, unique=True)
    summary = Column(Text, nullable=True)
    published = Column(DateTime, nullable=True)
    source_id = Column(Integer, ForeignKey("information_sources.id"))
    source = relationship("InformationSource")
    alerts = relationship("Alert", secondary="alert_news", passive_deletes=True, overlaps="news_items") #Evita que python busque eliminar huerfanos, confía en el delete Cascade de alerts


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    keyword = Column(String, nullable=False)
    synonyms = Column(String, default="[]")  
    iptc_category = Column(String, nullable=False)
    cron_expression = Column(String, default="*/5 * * * *")  # cada 5 min
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    #Cada Alert pertenece a un user, y un user puede tener varias alerts (alert.user y user.alerts)
    user = relationship("User", backref="alerts")
    #Un news_item puede pertenecer a varias alerts y una alert tener varios NewsItems
    news_items = relationship("NewsItem", secondary="alert_news", overlaps="alerts")


    #Para la generación de sinónimos
    def get_synonyms(self):
        return json.loads(self.synonyms or "[]")

    def set_synonyms(self, values):
        self.synonyms = json.dumps(values)

class AlertNews(Base):
    __tablename__ = "alert_news"

    id = Column(Integer, primary_key=True)
    
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"))
    news_item_id = Column(Integer, ForeignKey("news_items.id"))
