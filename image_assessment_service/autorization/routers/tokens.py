from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from image_assessment_service.autorization.models import schemas
from image_assessment_service.core.services.reset_token_service import *
from image_assessment_service.autorization.models.database import get_db
from image_assessment_service.autorization.controllers.tokens import create_token, send_reset_code_email
from image_assessment_service.autorization.controllers.users import update_user_password
from image_assessment_service.autorization.views.users import get_user_by_email
from image_assessment_service.core.dependencies.csrf import validate_csrf
from image_assessment_service.rate_limit import limiter
from pydantic import ValidationError
from sqlalchemy.orm import Session
from uuid import uuid4

router = APIRouter()
reset_tokens = {}


@router.post("/token", response_model=schemas.TokenUuid, status_code=201)
@limiter.limit("50/minute")
async def create_token_router(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
        csrf_valid: bool = Depends(validate_csrf)
):
    user_data = _parse_auth_form(form_data)

    access_token = create_token(db=db, user_data=user_data)

    return _build_token_response(access_token)


@router.post("/request")
async def request_reset(
        request: schemas.ResetRequest,
        db: Session = Depends(get_db)):

    user = get_user_by_email(request.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    token_obj = create_reset_token(db, request.email, 1)
    send_reset_code_email(
        email=user.email,
        code=str(token_obj.token),
        nickname=user.nickname
    )

    return {"message": "Reset link sent"}


@router.post("/confirm")
async def confirm_reset(confirm: schemas.ResetConfirm,
                        db: Session = Depends(get_db)):

    token_obj = get_valid_reset_token(db, confirm.token)
    if not token_obj:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_data = schemas.UserCreate(email=token_obj.email, password=confirm.new_password)
    update_user_password(db=db, user_data=user_data)

    mark_token_as_used(db, token_obj.id)

    return {"message": "Password updated successfully"}


def _parse_auth_form(form_data: OAuth2PasswordRequestForm) -> schemas.UserAuth:
    try:
        return schemas.UserAuth(
            email=form_data.username,
            password=form_data.password
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.errors()
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format"
        )


def _build_token_response(access_token):
    session_id = str(uuid4())

    return {
        "access_token": access_token["access_token"],
        "session_id": session_id,
        "token_type": "bearer"
    }