import json
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from image_assessment_service.autorization.controllers.utils import (
    get_current_user,
    require_role,
)
from image_assessment_service.autorization.models.core import User
from image_assessment_service.config import get_templates
from image_assessment_service.dependencies import get_container
from pydantic import BaseModel

admin_service = get_container().admin_service
aggregation_service = get_container().aggregation_service
annotation_service = get_container().annotation_service
task_service = get_container().task_service

router = APIRouter()

templates = get_templates()


### static ###


@router.get("/annotations/{annotation_id}")
async def annotation_page(request: Request, annotation_id: int):
    return templates.TemplateResponse(
        "annotation.html", {"request": request, "annotation_id": annotation_id}
    )


@router.get("/annotations/{annotation_id}/scores")
async def get_scores(request: Request, annotation_id: int):
    return templates.TemplateResponse(
        "scores.html", {"request": request, "annotation_id": annotation_id}
    )


### api ###


@router.delete("/api/annotations/{annotation_id}")
async def delete_annotation(
    request: Request,
    annotation_id: int,
    user: User = Depends(require_role("admin", "teacher")),
):
    annotation = await annotation_service.get_annotation(annotation_id)
    roles = [r.name for r in await admin_service.get_user_roles(user.id)]
    has_access = False
    if "admin" in roles:
        has_access = True
    elif "teacher" in roles:
        if await task_service.is_owner(annotation.task_id, user.id):
            has_access = True

    if has_access:
        return await annotation_service.delete_annotation(annotation_id)
    else:
        raise HTTPException(403)


@router.get("/api/annotations/{annotation_id}")
async def get_annotation(
    request: Request,
    annotation_id: int,
    response: Response,
    user: User = Depends(get_current_user),
):
    annotation = await annotation_service.get_annotation(annotation_id)
    roles = [r.name for r in await admin_service.get_user_roles(user.id)]
    has_access = False
    is_owner = False

    if await annotation_service.is_owner(annotation_id, user.id):
        has_access = True
        is_owner = True
    elif "admin" in roles:
        has_access = True
    elif "teacher" in roles and await task_service.is_owner(
        annotation.task_id, user.id
    ):
        has_access = True

    if has_access:
        response.headers["X-Annotation-Editable"] = str(is_owner).lower()
        return annotation
    else:
        raise HTTPException(403)


@router.get("/api/annotations/{annotation_id}/scores")
async def get_annotation(
    request: Request,
    annotation_id: int,
    user: User = Depends(get_current_user),
):
    annotation = await annotation_service.get_annotation(annotation_id)
    roles = [r.name for r in await admin_service.get_user_roles(user.id)]
    has_access = False

    if "admin" in roles or (
        "teacher" in roles and await task_service.is_owner(annotation.task_id, user.id)
    ):
        has_access = True

    if has_access:
        scores_file_path = await annotation_service.get_scores_path(annotation_id)
        return FileResponse(scores_file_path)
    else:
        raise HTTPException(403)


@router.post("/api/annotations/{annotation_id}/images/{image_name}")
async def save_annotations(
    request: Request,
    annotation_id: int,
    image_name: str,
    user: User = Depends(get_current_user),
):
    assert await annotation_service.is_owner(annotation_id, user.id), HTTPException(403)
    raw_json = await request.body()  # Получаем сырые данные
    # Массив с аннотациями вида [{'id': 1, 'label': 'dog', 'type': 'bbox', 'coords': [1400.5, 667, 1752.5, 811]}]
    data = json.loads(raw_json)
    await annotation_service.save(annotation_id, image_name, data)
    return {"status": "success"}


@router.get("/api/annotations/{annotation_id}/images/{image_name}")
async def get_annotations(
    request: Request,
    annotation_id: int,
    image_name: str,
    user: User = Depends(get_current_user),
):
    annotation = await annotation_service.get_annotation(annotation_id)
    roles = [r.name for r in await admin_service.get_user_roles(user.id)]
    has_access = False

    if await annotation_service.is_owner(annotation_id, user.id):
        has_access = True
    elif "admin" in roles:
        has_access = True
    elif "teacher" in roles and await task_service.is_owner(
        annotation.task_id, user.id
    ):
        has_access = True

    if has_access:
        return await annotation_service.get(annotation_id, image_name)
    else:
        raise HTTPException(403)


class AggregationRequest(BaseModel):
    annotation_ids: List[int]
    threshold_iou: float
    min_overlap: int


class AggregationResult(BaseModel):
    annotation_id: int
    quality_scores: Dict[int, float]  # annotation_id -> score


@router.post("/api/annotations/aggregate")
async def aggregate_annotations(
    request: Request,
    aggregation_request: AggregationRequest,
    user: User = Depends(require_role("admin", "teacher")),
):
    annotations = []
    for ann_id in aggregation_request.annotation_ids:
        ann = await annotation_service.get_annotation(ann_id)
        if ann is None:
            raise HTTPException(400)
        annotations.append(ann)

    if len(annotations) < 2:
        raise HTTPException(400)

    task_id = annotations[0].task_id
    for ann in annotations:
        if ann.task_id != task_id:
            raise HTTPException(400)

    if not await task_service.is_owner(task_id, user.id):
        raise HTTPException(400)

    ann_id = await aggregation_service.aggregate_annotations(
        annotations, aggregation_request.threshold_iou, aggregation_request.min_overlap
    )

    return AggregationResult(annotation_id=ann_id, quality_scores={})
