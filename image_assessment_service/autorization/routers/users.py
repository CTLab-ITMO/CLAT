from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Annotated

from image_assessment_service.core.dependencies.csrf import validate_csrf
from image_assessment_service.autorization.controllers.users import register as register_user, resend_confirmation_code, confirm_email
from image_assessment_service.autorization.models import schemas
from image_assessment_service.autorization.models.database import get_db
from image_assessment_service.autorization.secure import apikey_scheme
from image_assessment_service.autorization.views.users import get_users, get_user_by_token
from image_assessment_service.rate_limit import limiter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get('/', response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_users(db, skip=skip, limit=limit)


@router.post('/register/', response_model=schemas.LightUser, status_code=201)
@limiter.limit("50/minute")
def register(
        request: Request,
        user_data: schemas.UserCreate,
        db: Session = Depends(get_db),
        csrf_valid: bool = Depends(validate_csrf)
    ):
    return register_user(user_data=user_data, db=db)


@router.post('/resend_code/', status_code=200)
@limiter.limit("50/minute")
def resend_confirmation_code_route(
        request: Request,
        user_data: schemas.ResendConfirmEmailToken,
        db: Session = Depends(get_db),
        csrf_valid: bool = Depends(validate_csrf)
    ):
    resend_confirmation_code(email=user_data.email, db=db)
    return JSONResponse({
        "message": "Code sent"
    })


@router.post('/confirm_email/', status_code=200)
@limiter.limit("50/minute")
def confirm_email_route(
        request: Request,
        email_confirm: schemas.EmailConfirm,
        db: Session = Depends(get_db),
        csrf_valid: bool = Depends(validate_csrf)
    ):
    confirm_email(db=db, email=email_confirm.email, token=email_confirm.token)
    return JSONResponse({
        "message": "Email confirmed"
    })


@router.get('/self', response_model=schemas.LightUser)
def get_user_by_id(access_token: Annotated[str, Depends(apikey_scheme)], db: Session = Depends(get_db)):
    return get_user_by_token(access_token=access_token, db=db)
