
import os
import smtplib
from email.message import EmailMessage
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@newsradar.com")


def send_email(to_email: str, subject: str, body: str, html: Optional[str] = None) -> bool:
    if not SMTP_HOST:
        print("[EMAIL] SMTP no configurado, se omite el envío de correo")
        return False

    message = EmailMessage()
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    if html:
        message.add_alternative(html, subtype="html")

    try:
        if SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            if SMTP_USE_TLS:
                server.starttls()

        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)

        server.send_message(message)
        server.quit()
        print(f"[EMAIL] Enviado a {to_email} -> {subject}")
        return True
    except Exception as exc:
        print(f"[EMAIL] Error al enviar correo a {to_email}: {exc}")
        return False


def notify_user(alert, news_item=None):
    user = getattr(alert, "user", None)
    if not user or not getattr(user, "email", None):
        print(f"[NOTIFY] No se puede notificar al usuario de la alerta {alert.id}: usuario o email no disponible")
        return False

    subject = f"NewsRadar: nueva noticia detectada para alerta '{alert.name}'"
    body = f"Hola {getattr(user, 'first_name', 'usuario')},\n\n"
    body += f"Se ha detectado una nueva noticia que coincide con tu alerta '{alert.name}'.\n\n"
    if news_item is not None:
        body += f"Título: {news_item.title or 'Sin título'}\n"
        body += f"Enlace: {news_item.link or 'No disponible'}\n"
        body += f"Resumen: {news_item.summary or 'No hay resumen disponible'}\n\n"
    body += "Puedes ver más detalles en la aplicación NewsRadar.\n\n"
    body += "Saludos,\nNewsRadar"

    return send_email(user.email, subject, body)
