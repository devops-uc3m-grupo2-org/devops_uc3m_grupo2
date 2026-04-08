from datetime import datetime, timezone
from app.models.models import Notification, User

import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import joinedload

def notify_user(db):
    
    pending = (
    db.query(Notification)
    .options(joinedload(Notification.user))
    .filter(Notification.status == "pending")
    .all())
    for n in pending:
        print(f"[Notification] Sending Notification to {n.user.email}")

        try:
            user = db.query(User).filter(User.id == n.user_id).first()
            send_email(user.email, n.subject, n.body)
            n.status = "sent"
            n.sent_at = datetime.now(timezone.utc)

        except Exception:
            n.status = "failed"

def build_email_body(alert, news_item, user=None):
    source = news_item.source

    published = news_item.published
    if published:
        published_str = published.strftime("%d/%m/%Y %H:%M")
    else:
        published_str = "Fecha no disponible"

    body = f"""
    Actualización de alerta: {alert.name}

    Fecha: {published_str}

    Fuente: {source.name if source else 'Desconocida'}
    Medio: {source.medium if source else 'N/A'}

    Título: {news_item.title}

    Resumen: {news_item.summary or 'Sin resumen disponible'}

    Enlace: {news_item.link}

    """.strip()

    return body


def send_email(to_email: str, subject: str, body: str):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "100485446@gmail.com"
    SMTP_PASSWORD = "zjpi zibf hpms rgdm"

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)

        print(f"[EMAIL SENT] to {to_email}")

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        raise