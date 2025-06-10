from fastapi import APIRouter, Request
from image_assessment_service.config import get_templates

router = APIRouter()

templates = get_templates()


@router.get("/dashboard")
async def annotation_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
