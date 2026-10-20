import uuid

from fastapi import HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from starlette.status import HTTP_400_BAD_REQUEST

from image_assessment_service.autorization.models.core import User, Token
from image_assessment_service.autorization.models.schemas import UserAuth
from image_assessment_service.autorization.secure import pwd_context
from image_assessment_service.core.services.mail_service import send_email


def create_token(db: Session, user_data: UserAuth):
    user = _authenticate_user(db, user_data)
    _delete_previous_tokens(db, user)

    return _issue_token(db, user)


def send_reset_code_email(email: str, code: str, nickname: str) -> None:
    """Send 6-digit verification code to user"""

    body = f"""
    Hi {nickname},

    We received a request to reset your password.

    Your password reset code is:

    {code}

    The code expires in 1 hour. If you didn't request this, ignore this email.

    Best regards,
    The Image Assessment Service Team
    """
    send_email(email, body, "Password Reset Code")


def _authenticate_user(db: Session, user_data: UserAuth) -> User:
    user: User = db.scalar(select(User).where(User.email == user_data.email))
    if not user:
        raise _invalid_credentials_error()

    if not pwd_context.verify(user_data.password, user.hashed_password):
        raise _invalid_credentials_error()

    if user.email_confirmed_at is None:
        raise HTTPException(
            status_code=400,
            detail='Email not confirmed'
        )

    return user


def _invalid_credentials_error() -> HTTPException:
    return HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail='Incorrect password or username'
    )


def _delete_previous_tokens(db: Session, user: User) -> None:
    # Delete previous user tokens
    db.execute(
        delete(Token)
        .where(Token.user_id == user.id)
    )
    db.commit()


def _issue_token(db: Session, user: User):
    token: Token = Token(user_id=user.id, access_token=str(uuid.uuid4()))
    db.add(token)
    db.commit()

    return {"access_token": token.access_token}