import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog
from fastapi import HTTPException

logger = structlog.get_logger()


def send_email(email: str, content: str, subject: str) -> None:
    """Send 6-digit verification code to user"""
    msg = _build_message(email, content, subject)
    server = None
    try:
        server = _open_connection()
        server.sendmail(_sender_email(), email, msg.as_string())
    except Exception as e:
        logger.error(
            "Failed to send email",
            recipient=email,
            subject=subject,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to send email",
        ) from e
    finally:
        _close_connection(server)


def _build_message(email: str, content: str, subject: str):
    msg = MIMEMultipart()
    msg["From"] = _sender_email()
    msg["To"] = email
    msg["Subject"] = subject

    msg.attach(MIMEText(content, "plain"))

    return msg


def _open_connection():
    server = smtplib.SMTP(_smtp_host(), _smtp_port())
    server.starttls()
    server.login(_sender_email(), _email_password())
    return server


def _close_connection(server) -> None:
    if server is not None:
        server.quit()


def _smtp_host() -> str:
    return os.getenv('EMAIL_SMTP_SERVER')


def _smtp_port() -> int:
    return int(os.getenv('EMAIL_PORT'))


def _sender_email() -> str:
    return os.getenv('EMAIL')


def _email_password() -> str:
    return os.getenv('EMAIL_PASS')