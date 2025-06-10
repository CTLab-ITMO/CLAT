from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import HTTPException

import os

from image_assessment_service.autorization.models.core import User, Token
from image_assessment_service.autorization.models.schemas import UserAuth
from image_assessment_service.autorization.secure import pwd_context

import smtplib

from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from starlette.status import HTTP_400_BAD_REQUEST

import uuid

def create_token(db: Session, user_data:UserAuth):

    user: User = db.scalar(select(User).where(User.email == user_data.email))
    if not user:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail='User not found'
        )

    if not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail='Incorrect password or username'
        )

    # Delete previous user tokens
    db.execute(
        delete(Token)
        .where(Token.user_id == user.id)
    )
    db.commit()

    token: Token = Token(user_id=user.id, access_token=str(uuid.uuid4()))
    db.add(token)
    db.commit()
    return {"access_token": token.access_token}


def send_reset_code_email(email: str, code: str) -> None:
    """Send 6-digit verification code to user"""
    smtp_server = "smtp.mail.ru"
    port = 587
    sender_email = os.getenv('EMAIL')
    password = os.getenv('EMAIL_PASS')

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = "Your Password Reset Code"

    body = f"""
    Your password reset code is:

    {code}

    With best regards.
    """

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
    except Exception as e:
        print(f"Email sending failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email"
        )
    finally:
        server.quit()