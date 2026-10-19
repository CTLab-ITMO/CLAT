from fastapi import APIRouter, Depends, Request, HTTPException, status
from image_assessment_service.core.dependencies.csrf import get_csrf_service
from image_assessment_service.core.services.csrf_service import CSRFTokenService, CSRF
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post('/')
def get_csrf_token_api(
        request: Request,
        purpose: str = CSRF.Purpose.GENERAL.value,
        csrf_service: CSRFTokenService = Depends(get_csrf_service)
):
    session_id = _get_session_id(request)

    token = csrf_service.create_token(
        session_id=session_id,
        purpose=CSRF.Purpose(purpose)
    )

    return _build_token_response(token, purpose, csrf_service)


def _get_session_id(request: Request) -> str:
    session_id = request.state.session_id
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unset session_id"
        )

    return session_id


def _build_token_response(token: str, purpose: str, csrf_service: CSRFTokenService):
    return JSONResponse({
        "csrf_token": token,
        "purpose": purpose,
        "expires_in": csrf_service.token_ttl
    })