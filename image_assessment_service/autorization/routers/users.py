from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Annotated

from pathlib import Path

from image_assessment_service.autorization.controllers.users import register as register_user
from image_assessment_service.autorization.models import schemas
from image_assessment_service.autorization.models.database import get_db
from image_assessment_service.autorization.secure import apikey_scheme
from image_assessment_service.autorization.views.users import get_users, get_user_by_token


router = APIRouter()

@router.get('/', response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.post('/register/', response_model=schemas.LightUser, status_code=201)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    return register_user(user_data=user_data, db=db)

@router.get('/self', response_model=schemas.LightUser)
def get_user_by_id(access_token: Annotated[str, Depends(apikey_scheme)], db: Session = Depends(get_db)):
    return get_user_by_token(access_token=access_token, db=db)
