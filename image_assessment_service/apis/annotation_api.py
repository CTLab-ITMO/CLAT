import json
from typing import Dict, List, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from image_assessment_service.autorization.controllers.utils import (
    get_current_user,
    require_role,
)
from image_assessment_service.autorization.models.core import User
from image_assessment_service.config import get_templates
from image_assessment_service.dependencies import get_container
from image_assessment_service.validation import validate_annotation_data
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


@router.get("/annotations/{annotation_id}/export")
async def get_export_page(request: Request, annotation_id: int):
    return templates.TemplateResponse(
        "export.html", {"request": request, "annotation_id": annotation_id}
    )


### api ###


@router.delete("/api/annotations/{annotation_id}")
async def delete_annotation(
    request: Request,
    annotation_id: int,
    user: User = Depends(require_role("admin", "teacher")),
):
    annotation = await annotation_service.get_annotation(annotation_id)
    if not await _can_manage_annotation(user, annotation):
        raise HTTPException(403)

    return await annotation_service.delete_annotation(annotation_id)


@router.get("/api/annotations/{annotation_id}")
async def get_annotation(
    request: Request,
    annotation_id: int,
    response: Response,
    user: User = Depends(get_current_user),
):
    annotation = await annotation_service.get_annotation(annotation_id)
    is_owner = await annotation_service.is_owner(annotation_id, user.id)

    if not (is_owner or await _can_manage_annotation(user, annotation)):
        raise HTTPException(403)

    response.headers["X-Annotation-Editable"] = str(is_owner).lower()
    return annotation


@router.get("/api/annotations/{annotation_id}/scores")
async def get_annotation_scores(
    request: Request,
    annotation_id: int,
    user: User = Depends(get_current_user),
):
    annotation = await annotation_service.get_annotation(annotation_id)
    if not await _can_manage_annotation(user, annotation):
        raise HTTPException(403)

    scores_file_path = await annotation_service.get_scores_path(annotation_id)
    if not scores_file_path.exists():
        raise HTTPException(404, "Scores are not available yet")
    return FileResponse(scores_file_path)


class ExportRequest(BaseModel):
    export_format: Literal["json"]
    include_bbox: bool
    include_seg: bool
    include_cls: bool
    include_images: bool


@router.post("/api/annotations/{annotation_id}/export")
async def export_annotations(
    request: Request,
    annotation_id: int,
    exportRequest: ExportRequest,
    user: User = Depends(get_current_user),
):
    annotation = await annotation_service.get_annotation(annotation_id)
    if not await _can_manage_annotation(user, annotation):
        raise HTTPException(403)

    export_file_path = await _build_export(annotation_id, exportRequest)

    # Используем FileResponse с временным файлом
    return _export_file_response(export_file_path)


@router.post("/api/annotations/{annotation_id}/images/{image_name}")
async def save_annotations(
    request: Request,
    annotation_id: int,
    image_name: str,
    user: User = Depends(get_current_user),
):
    if not await annotation_service.is_owner(annotation_id, user.id):
        raise HTTPException(403)
    raw_json = await request.body()  # Получаем сырые данные
    # Массив с аннотациями вида [{'id': 1, 'label': 'dog', 'type': 'bbox', 'coords': [1400.5, 667, 1752.5, 811]}]
    data = json.loads(raw_json)
    validate_annotation_data(data)
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
    if not await _can_manage_annotation(user, annotation, allow_owner=True):
        raise HTTPException(403)

    return await annotation_service.get(annotation_id, image_name)


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
    annotations = await _load_annotations(aggregation_request.annotation_ids)
    _validate_same_task(annotations)

    if not await task_service.is_owner(annotations[0].task_id, user.id):
        raise HTTPException(400)

    ann_id = await aggregation_service.aggregate_annotations(
        annotations, aggregation_request.threshold_iou, aggregation_request.min_overlap
    )

    return AggregationResult(annotation_id=ann_id, quality_scores={})


def _export_file_response(export_file_path):
    # Используем FileResponse с временным файлом
    return FileResponse(
        export_file_path,
        media_type="application/zip",
        filename=export_file_path.name,
    )


async def _build_export(annotation_id: int, exportRequest: ExportRequest):
    return await annotation_service.export(
        annotation_id,
        exportRequest.export_format,
        exportRequest.include_bbox,
        exportRequest.include_seg,
        exportRequest.include_cls,
        exportRequest.include_images,
    )


async def _can_manage_annotation(user: User, annotation, allow_owner: bool = False) -> bool:
    roles = [r.name for r in await admin_service.get_user_roles(user.id)]

    if allow_owner and await annotation_service.is_owner(annotation.annotation_id, user.id):
        return True
    if "admin" in roles:
        return True
    if "teacher" in roles and await task_service.is_owner(annotation.task_id, user.id):
        return True

    return False


async def _load_annotations(annotation_ids: List[int]):
    annotations = []
    for ann_id in annotation_ids:
        ann = await annotation_service.get_annotation(ann_id)
        if ann is None:
            raise HTTPException(400)
        annotations.append(ann)

    return annotations


def _validate_same_task(annotations) -> None:
    if len(annotations) < 2:
        raise HTTPException(400)

    task_id = annotations[0].task_id
    for ann in annotations:
        if ann.task_id != task_id:
            raise HTTPException(400)