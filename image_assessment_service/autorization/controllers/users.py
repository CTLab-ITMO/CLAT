from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST

from image_assessment_service.autorization.models.core import User
from image_assessment_service.autorization.models.schemas import UserCreate, ResetConfirm
from image_assessment_service.autorization.secure import pwd_context
from image_assessment_service.autorization.controllers.utils import generate_nickname

def register(db: Session, user_data: UserCreate):
    if db.scalar(select(User).where(User.email == user_data.email)):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="User with this email already registered",
        )

    user = User(email=user_data.email)
    user.hashed_password = pwd_context.hash(user_data.password)

    nickname_unique = False
    while not nickname_unique:
        nickname = generate_nickname()  # Generate a nickname
        # Check if the nickname already exists in the database
        existing_nickname = db.scalar(select(User).where(User.nickname == nickname))
        if not existing_nickname:
            nickname_unique = True  # Return the nickname if it's unique

    user.nickname = nickname
    db.add(user)
    db.commit()

    return {
        "id": user.id,
        "email": user.email
    }

def update_user_password(db: Session, user_data: UserCreate):
    """Update user's password in the database"""
    # Hash the new password
    hashed_password = pwd_context.hash(user_data.password)

    # Find the user
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise ValueError("User with this email does not exist")

    user.hashed_password = hashed_password
    # Commit changes
    db.commit()
    db.refresh(user)
    user = db.query(User).filter(User.email == user_data.email).first()
