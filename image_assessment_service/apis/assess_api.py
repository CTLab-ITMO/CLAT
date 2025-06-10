from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from image_assessment_service.config import get_config, get_templates

config = get_config().tasks
templates = get_templates()
router = APIRouter()


### static ###


@router.get("/assess/main", response_class=HTMLResponse)
async def task_page(request: Request):
    return templates.TemplateResponse("assess.html", {"request": request})
