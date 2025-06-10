from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import FileResponse

from image_assessment_service.services import SamplesService
from image_assessment_service.storages import Storages
from image_assessment_service.config import get_config
from image_assessment_service.autorization.models.database import get_db
from image_assessment_service.autorization.controllers.image_ratings import get_assess_statistics

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os

SQLALCHEMY_DATABASE_URL = get_config().postgres.get_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

service = None
_startup_ran = False

tech_api = APIRouter()
# tech_api = APIRouter(dependencies=[Depends(get_current_user)])

@tech_api.on_event("startup")
async def startup():
    global _startup_ran, service
    if _startup_ran:
        return

    _startup_ran = True
    db = SessionLocal()
    service = SamplesService(code="tech", db=db)

@tech_api.get('/get')
async def get(token: str, db: Session = Depends(get_db), code: str = "tech"):
    fid, user_answers = service.rand_fid(code=code, token=token, db=db)
    if fid is None:
        return {
            'fid': 'null',
            'metrics': {
                'all': service.all(),
                'size': service.size(),
                'answers': service.answers(),
                'user_answers': user_answers
            }
        }

    f = service.get(fid, code="tech")
    return {
        'fid': fid,
        'file': {
            'storage': f[0],
            'path': f[1],
            'name': f[2]
        },
        'metrics': {
            'all': service.all(),
            'size': service.size(),
            'answers': service.answers(),
            'user_answers': user_answers
        }
    }

@tech_api.get('/file')
def get_file(s: str, p: str, f: str):
    full_path = Storages().get(code=s).to_path(p, f)
    return FileResponse(full_path)

@tech_api.post('/mark')
def mark_yes(type: str, fid: str, token: str, db: Session = Depends(get_db), code: str = "tech"):
    if fid is None or len(fid) == 0:
        return
    service.mark(fid, type, code=code, db=db, token=token)

@tech_api.get('/stats')
async def get_stats(token: str, db: Session = Depends(get_db)):
    response = get_assess_statistics(token, db=db)
    return response


