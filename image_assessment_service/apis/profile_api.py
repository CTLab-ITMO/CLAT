from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from image_assessment_service.autorization.controllers.utils import get_current_user
from image_assessment_service.autorization.models.core import User
from image_assessment_service.config import get_config, get_templates
from image_assessment_service.dependencies import get_container

admin_service = get_container().admin_service
annotation_service = get_container().annotation_service

config = get_config().tasks
templates = get_templates()
router = APIRouter()


### static ###


@router.get("/profile", response_class=HTMLResponse)
async def task_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


### api ###


@router.get("/api/user-annotations")
async def get_annotations(request: Request, user: User = Depends(get_current_user)):
    annotations = await annotation_service.get_annotations(user.id)
    return annotations


@router.get("/api/current-user")
async def get_user(request: Request, user: User = Depends(get_current_user)):
    roles = [r.name for r in await admin_service.get_user_roles(user.id)]
    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "nickname": user.nickname,
        "roles": roles,
    }
