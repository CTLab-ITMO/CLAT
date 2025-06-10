import asyncio
import datetime
import os
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile
from image_assessment_service.autorization.models.core import Task
from image_assessment_service.config import get_config
from image_assessment_service.core.services.task_service import TaskSpec


class DataUploaderServiceImpl:
    def __init__(self, db_session):
        self.db_session = db_session
        self.base_path = Path(get_config().tasks.base_path) / "tasks_data"
        os.makedirs(self.base_path, exist_ok=True)

    def get_task_dir(self, task_id):
        return os.path.join(self.base_path, str(task_id))

    def get_file_path(self, task_id, file_name):
        return os.path.join(self.base_path, str(task_id), file_name)

    async def start_cleanup_daemon(self):
        asyncio.create_task(self.cleanup_task())

    async def cleanup_task(self):
        print("DataUploadService clean up daemon started")
        while True:
            self.cleanup_old_files()
            await asyncio.sleep(1)

    async def init_upload(self, metadata: dict, user_id: int) -> int:
        deadline = datetime.fromisoformat(metadata["deadline"])
        task_id = None
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
            task_id = new_task.task_id

        task_dir = self.get_task_dir(task_id)
        os.makedirs(task_dir, exist_ok=False)
        task_file = self.get_file_path(task_id, "task.yaml")

        task_spec = TaskSpec.from_dict(metadata)
        task_spec.save_to_yaml(task_file)

        return task_id

    async def upload_file(self, task_id: int, file: UploadFile):
        task_dir = self.get_task_dir(task_id)
        if not os.path.exists(task_dir):
            raise HTTPException(404, "Task not found")

        file_path = self.get_file_path(task_id, file.filename)
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
        # """Очищает старые файлы в директории загрузок"""
        # now = datetime.now()
        # for filename in os.listdir(self.base_path):
        #     filepath = os.path.join(self.base_path, filename)
        #     file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        #     if (now - file_time).hours > older_than_hours:
        #         try:
        #             os.remove(filepath)
        #         except Exception as e:
        #             print(f"Ошибка при удалении файла {filename}: {str(e)}")
