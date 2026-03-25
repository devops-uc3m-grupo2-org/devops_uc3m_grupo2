from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


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
