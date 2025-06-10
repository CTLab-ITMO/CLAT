from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from image_assessment_service.autorization.models import schemas
from image_assessment_service.autorization.models.database import get_db
from image_assessment_service.autorization.controllers.tokens import create_token, send_reset_code_email
from image_assessment_service.autorization.controllers.users import update_user_password
from image_assessment_service.autorization.models.schemas import UserCreate
from image_assessment_service.autorization.views.users import get_user_by_email

from sqlalchemy.orm import Session

from uuid import uuid4

import pathlib

import secrets

STATIC_FILES_PATH = pathlib.Path(__file__).parents[2] / "static" / "login" / "index.html"

router = APIRouter()
templates = Jinja2Templates(directory=STATIC_FILES_PATH / "login")
reset_tokens = {}

@router.post("/token", response_model=schemas.TokenUuid, status_code=201)
async def create_token_router(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    user_data = schemas.UserAuth(
            email=form_data.username,
            password=form_data.password
        )

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = str(uuid4())  # ← Unique for every login
    access_token = create_token(db=db, user_data=user_data)

    return {
        "access_token": access_token["access_token"],
        "session_id": session_id,  # ← Send to frontend
        "token_type": "bearer"
    }


@router.post("/request")
async def request_reset(
        request: schemas.ResetRequest,
        db: Session = Depends(get_db)):

    # Check if email exists
    user = get_user_by_email(request.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    # Generate token (valid for 1 hour)
    token = secrets.token_urlsafe(16)
    reset_tokens[token] = {
        "email": request.email,
        "expires": datetime.now() + timedelta(hours=1)
    }
    # Send email
    send_reset_code_email(
        email=user.email,
        code=str(token)
    )

    return {"message": "Reset link sent"}


@router.post("/confirm")
async def confirm_reset(confirm: schemas.ResetConfirm,
                        db: Session = Depends(get_db)):
    token_data = reset_tokens.get(confirm.token)

    # Validate token
    if not token_data or token_data["expires"] < datetime.now():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    email = token_data.get("email")

    # Update password
    user_data = UserCreate(email=email, password=confirm.new_password)
    update_user_password(db=db, user_data=user_data)

    # Cleanup
    del reset_tokens[confirm.token]

    return {"message": "Password updated successfully"}
