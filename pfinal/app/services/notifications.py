
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


def notify_alert(alert, matched_news: list) -> bool:
    from datetime import datetime
    user = getattr(alert, "user", None)
    if not user or not getattr(user, "email", None):
        print(f"[NOTIFY] Alerta {alert.id}: usuario o email no disponible")
        return False

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    subject = f"Actualización de {alert.name} en {now}"

    body = f"Hola {getattr(user, 'first_name', 'usuario')},\n\n"
    body += f"Se han detectado {len(matched_news)} noticia(s) que coinciden con tu alerta '{alert.name}'.\n\n"
    for item in matched_news:
        body += f"- Título: {item.title or 'Sin título'}\n"
        body += f"  Fuente: {getattr(getattr(item, 'channel', None), 'url', 'desconocida')}\n"
        body += f"  Fecha: {item.published or 'desconocida'}\n"
        body += f"  Resumen: {(item.summary or '')[:200]}\n"
        body += f"  Enlace: {item.link or ''}\n\n"
    body += "Puedes ver más detalles en la aplicación NewsRadar.\n\nSaludos,\nNewsRadar"

    return send_email(user.email, subject, body)


def send_reset_email(to_email: str, first_name: str, token: str, base_url: str) -> bool:
    subject = "NewsRadar: recuperación de contraseña (válido 1h)"
    link = f"{base_url}/?reset_token={token}"
    body = (
        f"Hola {first_name},\n\n"
        f"Has solicitado recuperar tu contraseña en NewsRadar.\n"
        f"Haz click en el siguiente enlace para crear una nueva:\n\n"
        f"{link}\n\n"
        f"Este enlace caduca en 1 hora.\n"
        f"Si no solicitaste esto, ignora este email.\n\n"
        f"Saludos,\nNewsRadar"
    )
    return send_email(to_email, subject, body)


def send_verification_email(to_email: str, first_name: str, token: str, base_url: str) -> bool:
    subject = "NewsRadar: verifica tu cuenta (válido 24h)"
    link = f"{base_url}/api/v1/auth/verify?token={token}"
    body = f"Hola {first_name},\n\n"
    body += f"Gracias por registrarte en NewsRadar. Verifica tu cuenta haciendo click en el siguiente enlace:\n\n"
    body += f"{link}\n\n"
    body += "Este enlace caduca en 24 horas.\n\nSaludos,\nNewsRadar"
    return send_email(to_email, subject, body)
