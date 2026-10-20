from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session

from image_assessment_service.core.services.csrf_service import CSRFTokenService
from image_assessment_service.autorization.models.database import get_db
from image_assessment_service.autorization.models.core import CSRF


def get_csrf_service(db: Session = Depends(get_db)) -> CSRFTokenService:
    return CSRFTokenService(db)


async def validate_csrf(
        request: Request,
        csrf_service: CSRFTokenService = Depends(get_csrf_service),
        purpose: str = CSRF.Purpose.GENERAL.value
) -> bool:
    session_id = _get_session_id(request)
    csrf_token = await _extract_csrf_token(request)

    _ensure_csrf_valid(csrf_service, csrf_token, session_id, purpose)

    return True


def _get_session_id(request: Request) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=403, detail="Session required")

    return session_id


async def _extract_csrf_token(request: Request) -> str:
    csrf_token = request.headers.get("X-CSRF-Token")
    if csrf_token:
        return csrf_token

    return await _extract_body_token(request)


async def _extract_body_token(request: Request) -> str:
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        return form.get("csrf_token")

    if "application/json" in content_type:
        return await _extract_json_token(request)

    return None


async def _extract_json_token(request: Request) -> str:
    try:
        body = await request.json()
        return body.get("csrf_token")
    except Exception:
        return None


def _ensure_csrf_valid(
        csrf_service: CSRFTokenService,
        csrf_token: str,
        session_id: str,
        purpose: str
) -> None:
    if not csrf_token:
        raise HTTPException(status_code=403, detail="CSRF token required")

    if not csrf_service.validate_token(csrf_token, session_id, purpose):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    if not csrf_service.use_token(csrf_token, session_id, purpose):
        raise HTTPException(status_code=403, detail="CSRF token already used")