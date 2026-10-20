from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import secrets
from image_assessment_service.autorization.models.core import PasswordResetToken


def create_reset_token(db: Session, email: str, expires_hours: int = 1) -> PasswordResetToken:
    _invalidate_old_tokens(db, email)

    db_token = _build_token(db, email, expires_hours)

    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_valid_reset_token(db: Session, token: str) -> Optional[PasswordResetToken]:
    return db.query(PasswordResetToken) \
        .filter(PasswordResetToken.token == token) \
        .filter(PasswordResetToken.used_at.is_(None)) \
        .filter(PasswordResetToken.expires_at > datetime.utcnow()) \
        .first()


def mark_token_as_used(db: Session, token_id: int) -> None:
    """Mark a token as used"""
    db.query(PasswordResetToken) \
        .filter(PasswordResetToken.id == token_id) \
        .update({"used_at": datetime.utcnow()})
    db.commit()


def _invalidate_old_tokens(db: Session, email: str) -> None:
    db.query(PasswordResetToken) \
        .filter(PasswordResetToken.email == email) \
        .filter(PasswordResetToken.used_at.is_(None)) \
        .filter(PasswordResetToken.expires_at > datetime.utcnow()) \
        .update({"used_at": datetime.utcnow()})


def _build_token(db: Session, email: str, expires_hours: int) -> PasswordResetToken:
    token = secrets.token_urlsafe(16)
    expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

    return PasswordResetToken(
        token=token,
        email=email,
        expires_at=expires_at
    )