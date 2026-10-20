import asyncio
import os
from pathlib import Path

from dateutil.parser import isoparse
from fastapi import HTTPException, UploadFile
from image_assessment_service.assessment.services.detection.service import DetectionService
from image_assessment_service.autorization.models.core import Task
from image_assessment_service.config import get_config
from image_assessment_service.core.services.task_service import TaskSpec
from .consts import TaskFileTypes


class DataUploaderServiceImpl:
    def __init__(self, db_session):
        self.db_session = db_session
        self.base_path = Path(DetectionService().base_path) / "tasks_data"
        os.makedirs(self.base_path, exist_ok=True)

    async def start_cleanup_daemon(self):
        asyncio.create_task(self.cleanup_task())

    async def cleanup_task(self):
        print("DataUploadService clean up daemon started")
        while True:
            self.cleanup_old_files()
            await asyncio.sleep(1)

    async def init_upload(self, metadata: dict, user_id: int) -> int:
        deadline = isoparse(metadata["deadline"])

        task_id = self._create_task(metadata, user_id, deadline)
        self._create_task_dirs(task_id)
        self._save_task_spec(metadata, task_id)

        return task_id

    async def upload_file(self, task_id: int, file: UploadFile, file_type: str):
        task_dir = self.get_task_dir(task_id)
        if not os.path.exists(task_dir):
            raise HTTPException(404, "Task not found")

        file_path = self.get_file_path(task_id, file_type, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

    async def finish_upload(self, task_id: int):
        with self.db_session() as db:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task is None:
                raise HTTPException(404, "Task not found")
            task.status = "moderation"
            db.commit()

    def cleanup_old_files(self, older_than_hours: int = 1):
        pass

    def _create_task(self, metadata: dict, user_id: int, deadline) -> int:
        with self.db_session() as db:
            new_task = Task(
                user_id=user_id,
                status="uploading",
                annotators_count=metadata["annotators_count"],
                days_to_complete=metadata["days_to_complete"],
                deadline=deadline,
            )
            db.add(new_task)
            db.commit()
            return new_task.task_id

    def _create_task_dirs(self, task_id: int) -> None:
        task_dir = self.get_task_dir(task_id)
        os.makedirs(task_dir, exist_ok=False)
        for file_type in TaskFileTypes.ALL_FILE_TYPES:
            os.makedirs(self.get_task_dir(task_id, file_type), exist_ok=False)

    def _save_task_spec(self, metadata: dict, task_id: int) -> None:
        task_file = self.get_file_path(task_id, TaskFileTypes.FILE_TYPE_SETTINGS, "task.yaml")

        files_data = metadata.get('files', dict()).get(TaskFileTypes.FILE_TYPE_IMAGE, dict())
        if files_data:
            metadata['num_images'] = files_data.get("num_files", 0)
            metadata['image_names'] = files_data.get("file_names", [])

        task_spec = TaskSpec.from_dict(metadata)
        task_spec.save_to_yaml(task_file)

    def get_task_dir(self, task_id: int, file_type: str | None = None):
        return os.path.join(self.base_path, str(task_id)) if file_type is None \
            else os.path.join(self.base_path, str(task_id), file_type)

    def get_file_path(self, task_id: int, file_type: str, file_name: str):
        return os.path.join(self.base_path, str(task_id), file_type, file_name)
