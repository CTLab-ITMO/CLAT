import json

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from image_assessment_service.autorization.controllers.utils import (
    get_current_user,
    require_role,
)
from image_assessment_service.config import get_config, get_templates
from image_assessment_service.dependencies import get_container
from image_assessment_service.validation import validate_image_name
from image_assessment_service.core.services.consts import TaskFileTypes
from image_assessment_service.autorization.models.core import User

admin_service = get_container().admin_service
annotation_service = get_container().annotation_service
data_uploader_service = get_container().data_uploader_service
task_service = get_container().task_service

templates = get_templates()
router = APIRouter()

### static ###


@router.get("/tasks/manage/{task_id}", response_class=HTMLResponse)
async def manage_task_page(request: Request, task_id: int):
    return templates.TemplateResponse(
        "tasks/managed-task.html", {"request": request, "task_id": task_id}
    )


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
async def task_page(request: Request, task_id: int):
    return templates.TemplateResponse(
        "tasks/task.html",
        {"request": request, "task_id": task_id},
    )


@router.get("/create-task", response_class=HTMLResponse)
async def create_task_page(request: Request):
    return templates.TemplateResponse("create-task.html", {"request": request})


### api ###


@router.get("/api/tasks/{task_id}/annotations")
async def list_annotations(
    request: Request, task_id: int, user: User = Depends(get_current_user)
):
    roles = [r.name for r in await admin_service.get_user_roles(user.id)]
    has_access = False
    if "admin" in roles:
        has_access = True
    elif "teacher" in roles:
        if await task_service.is_owner(task_id, user.id):
            has_access = True

    if has_access:
        return await annotation_service.get_task_annotations_with_users(task_id)
    else:
        raise HTTPException(403)


@router.post("/api/tasks/{task_id}/create-annotation")
async def create_annotation(
    request: Request, task_id: int, user: User = Depends(get_current_user)
):
    annotation_id = await annotation_service.create_annotation(task_id, user.id)
    return {"annotation_id": annotation_id}


@router.get("/api/tasks/{task_id}/annotation-status")
async def annotation_status(
    request: Request, task_id: int, user: User = Depends(get_current_user)
):
    return await annotation_service.get_annotation_status(task_id, user.id)


@router.get("/api/tasks")
async def list_tasks(request: Request):
    task_specs = await task_service.list_full_tasks()
    return task_specs


@router.get("/api/tasks/{task_id}/images/{image_name}")
async def task_image(request: Request, task_id: int, image_name: str):
    validate_image_name(image_name)
    image_path = await task_service.get_image_path(task_id, image_name)
    return FileResponse(image_path)


@router.get("/api/tasks/{task_id}")
async def task_detail(request: Request, task_id: int):
    task = await task_service.get_full_task(task_id)
    if task is None:
        return HTTPException(404)
    return task


# admin or teacher only
@router.delete("/api/tasks/{task_id}")
async def delete_task(
    request: Request,
    task_id: int,
    user: User = Depends(get_current_user),
):
    roles = [r.name for r in await admin_service.get_user_roles(user.id)]
    has_access = False
    if "admin" in roles:
        has_access = True
    elif "teacher" in roles:
        if await task_service.is_owner(task_id, user.id):
            has_access = True

    if has_access:
        return await task_service.delete(task_id)
    else:
        raise HTTPException(403)


@router.post("/api/tasks/init-upload")
async def init_upload(
    request: Request, user: User = Depends(require_role("admin", "teacher"))
):
    print(f"user {user.nickname} creates task")
    try:
        raw_json = await request.body()  # Получаем сырые данные
        data = json.loads(raw_json)
        # {"title":"a","description":"g","instructions":"j","bbox_labels":[],"segmentation_labels":[]}
        task_id = await data_uploader_service.init_upload(data, user.id)
        print("inited task upload, id =", task_id)
        return {"taskId": task_id}
    except Exception as e:
        print(e)
        return HTTPException(400, e)


@router.post("/api/tasks/{task_id}/upload-file")
async def upload_file(
    request: Request,
    task_id: int,
    file: UploadFile,
    user: User = Depends(require_role("admin", "teacher")),
):
    try:
        file_type = request.query_params.get('file_type')

        _validate_file_type(file_type)

        if file_type == TaskFileTypes.FILE_TYPE_IMAGE:
            await _upload_image_file(task_id, file)
        if file_type == TaskFileTypes.FILE_TYPE_SEGMENTATION_DRAFT:
            await _upload_segmentation_draft(task_id, file)

        return {"status": "success"}
    except Exception as e:
        return HTTPException(400, e)


@router.post("/api/tasks/{task_id}/finish-upload")
async def finish_upload(
    task_id: int, user: User = Depends(require_role("admin", "teacher"))
):
    try:
        await data_uploader_service.finish_upload(task_id)
        print("finished task upload, id =", task_id)
        return {"status": "success"}
    except Exception as e:
        return HTTPException(400, e)


def _validate_file_type(file_type) -> None:
    if file_type not in TaskFileTypes.VALID_FILE_TYPES:
        raise HTTPException(400, "Невалидный тип изображения")


async def _upload_image_file(task_id: int, file: UploadFile) -> None:
    validate_image_name(file.filename)
    await data_uploader_service.upload_file(task_id, file, TaskFileTypes.FILE_TYPE_IMAGE)


async def _upload_segmentation_draft(task_id: int, file: UploadFile) -> None:
    content = await file.read()
    draft_data = json.loads(content)
    if not isinstance(draft_data, dict):
        raise HTTPException(400, "illegal JSON file format")

    for image_name, data in draft_data.items():
        filename = f"{image_name}.json"
        json_file = __dict_to_uploadfile(data, filename)
        await data_uploader_service.upload_file(task_id, json_file, TaskFileTypes.FILE_TYPE_SEGMENTATION_DRAFT)


def __dict_to_uploadfile(data: dict, filename: str) -> UploadFile:
    from io import BytesIO
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    file_like = BytesIO(json_bytes)

    return UploadFile(
        filename=filename,
        file=file_like
    )