from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from image_assessment_service.config import get_config, get_templates
from image_assessment_service.assessment.features_meta import FEATURE_META

templates = get_templates()
router = APIRouter()


### static ###


@router.get("/assess/main", response_class=HTMLResponse)
async def task_page(request: Request):
    config = get_config()
    features = []
    for code, meta in FEATURE_META.items():
        cfg = config.feature_config(code)
        if cfg is not None and cfg.enabled:
            features.append({"code": code, **meta})
    return templates.TemplateResponse("assess.html", {"request": request, "features": features})
