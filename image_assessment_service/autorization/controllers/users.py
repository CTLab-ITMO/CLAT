from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST

from image_assessment_service.autorization.models.core import User
from image_assessment_service.autorization.models.schemas import UserCreate
from image_assessment_service.autorization.secure import pwd_context
from image_assessment_service.autorization.controllers.utils import generate_nickname
from image_assessment_service.core.services.mail_service import send_email
from datetime import datetime

import uuid

__NICKNAME_GEN_ATTEMPTS = 100


def register(db: Session, user_data: UserCreate):
    _ensure_email_available(db, user_data.email)

    user = _create_user(db, user_data)

    try:
        __send_confirmation_mail(user)
    except HTTPException:
        db.rollback()
        raise

    db.commit()

    return {
        "id": user.id,
        "email": user.email
    }


def resend_confirmation_code(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="User with this email does not exist"
        )
    if user.email_confirmed_at is not None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Email already confirmed"
        )

    user.email_confirm_token = str(uuid.uuid4())

    db.commit()
    db.refresh(user)

    __send_confirmation_mail(user)


def confirm_email(db: Session, email: str, token: str):
    user = db.query(User).filter(User.email_confirm_token == token).first()
    if not user or user.email != email:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Incorrect token"
        )
    if user.email_confirmed_at is not None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Email already confirmed"
        )

    user.email_confirmed_at = datetime.utcnow()
    user.email_confirm_token = None

    db.commit()
    db.refresh(user)


def update_user_password(db: Session, user_data: UserCreate):
    """Update user's password in the database"""
    hashed_password = pwd_context.hash(user_data.password)

    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise ValueError("User with this email does not exist")

    user.hashed_password = hashed_password
    db.commit()
    db.refresh(user)


def _ensure_email_available(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if user and user.email_confirmed_at is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Email not confirmed",
        )
    if user:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="User with this email already registered",
        )


def _create_user(db: Session, user_data: UserCreate) -> User:
    user = User(
        email=user_data.email,
        hashed_password=pwd_context.hash(user_data.password),
        nickname=__generate_unique_username(db),
        email_confirm_token=str(uuid.uuid4())
    )

    db.add(user)
    db.flush()  # Получаем id и токен, но не коммитим до успешной отправки письма

    return user


def __send_confirmation_mail(user: User) -> None:
    body = f"""
        Hi {user.nickname},

        Thanks for registering with Image Assessment Service.

        Your email confirmation code is:

        {user.email_confirm_token}

        If you didn't request this, you can ignore this email.

        Best regards,
        The Image Assessment Service Team
        """
    send_email(user.email, body, "Confirm your email")


def __generate_unique_username(db: Session) -> str:
    for _ in range(__NICKNAME_GEN_ATTEMPTS):
        nickname = generate_nickname()
        existing_nickname = db.scalar(select(User).where(User.nickname == nickname))
        if not existing_nickname:
            return nickname
    raise HTTPException(
        status_code=500,
        detail=f"Failed to generate unique username in {__NICKNAME_GEN_ATTEMPTS} attempts"
    )