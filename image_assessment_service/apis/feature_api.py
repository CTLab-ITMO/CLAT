from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from image_assessment_service.assessment.services.registry import get_feature
from image_assessment_service.autorization.controllers.image_ratings import get_assess_statistics
from image_assessment_service.autorization.models.database import get_db
from image_assessment_service.storages import Storages


def _require_feature(code: str):
    feature = get_feature(code)
    if feature is None or not feature.enabled:
        raise HTTPException(503, f"Assessment feature '{code}' is not enabled")
    return feature


def _default_file_info(f) -> dict:
    return {'storage': f[0], 'path': f[1], 'name': f[2]}


def _metrics(feature, user_answers: int) -> dict:
    return {
        'all': feature.all(),
        'size': feature.size(),
        'answers': feature.answers(),
        'user_answers': user_answers,
    }


def _finished_response(feature, user_answers: int) -> dict:
    return {'fid': 'null', 'metrics': _metrics(feature, user_answers)}


def _sample_response(feature, fid: str, user_answers: int, file_info: Optional[Callable]) -> dict:
    file_info = file_info or _default_file_info
    f = feature.get(fid)
    return {'fid': fid, 'file': file_info(f), 'metrics': _metrics(feature, user_answers)}


def create_assessment_router(code: str, file_info: Optional[Callable] = None) -> APIRouter:
    """Создаёт тонкий APIRouter для фичи оценки: /get, /file, /mark, /stats."""
    router = APIRouter()

    @router.get('/get')
    async def get(token: str, db: Session = Depends(get_db)):
        feature = _require_feature(code)
        fid, user_answers = feature.rand_fid(token=token, db=db)
        if fid is None:
            return _finished_response(feature, user_answers)
        return _sample_response(feature, fid, user_answers, file_info)

    @router.get('/file')
    def get_file(s: str, p: str, f: str):
        full_path = Storages().get(code=s).to_path(p, f)
        return FileResponse(full_path)

    @router.post('/mark')
    def mark_yes(type: str, fid: str, token: str, db: Session = Depends(get_db)):
        if fid is None or len(fid) == 0:
            return
        feature = _require_feature(code)
        feature.mark(fid, type, token=token, db=db)

    @router.get('/stats')
    async def get_stats(token: str, db: Session = Depends(get_db)):
        return get_assess_statistics(token, db=db)

    return router