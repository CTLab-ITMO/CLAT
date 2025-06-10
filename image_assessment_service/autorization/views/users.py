from fastapi import HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import select

from starlette.status import HTTP_401_UNAUTHORIZED

from image_assessment_service.autorization.models import core

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(core).offset(skip).limit(limit).all()

def get_user_by_token(access_token: str, db: Session):
    token = db.scalar(select(core.Token).where(core.Token.access_token == access_token))
    if token:
        return {
            "id": token.user.id,
            "email": token.user.email
        }

    else:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="UNAUTHORIZED"
        )

def get_user_by_email(email: str, db: Session):
    return db.scalar(select(core.User).where(core.User.email == email))