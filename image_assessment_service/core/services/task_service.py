import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from image_assessment_service.autorization.models.core import Annotation, Task
from image_assessment_service.config import get_config
from image_assessment_service.core.storage import Storage


@dataclass
class TaskSpec:
    title: int
    description: str
    num_images: int
    bbox_labels: Optional[List[str]]
    segmentation_labels: Optional[List[str]]
    image_names: List[str]
    instructions: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует объект Task в словарь"""
        return {
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "num_images": self.num_images,
            "bbox_labels": self.bbox_labels,
            "segmentation_labels": self.segmentation_labels,
            "image_names": self.image_names,
        }

    def save_to_yaml(self, output_file: str) -> None:
        """Сохраняет задачу в YAML файл"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskSpec":
        """Создает объект TaskSpec из словаря"""
        return cls(
            title=data["title"],
            description=data["description"],
            num_images=data["num_images"],
            bbox_labels=data["bbox_labels"],
            segmentation_labels=data["segmentation_labels"],
            image_names=data.get("image_names"),
            instructions=data.get("instructions"),
        )

    @classmethod
    def from_yaml(cls, input_file: str) -> "TaskSpec":
        """Загружает задачу из YAML файла"""
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return cls.from_dict(data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл {input_file} не найден")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Ошибка при чтении YAML: {e}")
        except KeyError as e:
            raise ValueError(f"Отсутствует обязательное поле: {e}")


@dataclass
class FullTask:
    """
    models.core.Task + TaskSpec
    """

    id: int
    user_id: int
    status: str
    created_at: datetime
    days_to_complete: int
    deadline: datetime

    title: str = None
    description: str = None
    num_images: int = None
    bbox_labels: Optional[List[str]] = None
    segmentation_labels: Optional[List[str]] = None
    image_names: List[str] = None
    instructions: Optional[str] = None

    @classmethod
    def partial(cls, task: Task, **kwargs):
        return cls(
            id=task.task_id,
            user_id=task.user_id,
            status=task.status,
            created_at=task.created_at,
            days_to_complete=task.days_to_complete,
            deadline=task.deadline,
            **kwargs,
        )

    @classmethod
    def get(cls, task: Task, spec: TaskSpec):
        return cls.partial(task, **asdict(spec))


class TaskServiceImpl:
    def __init__(self, db_session):
        self.db_session = db_session
        base_path = Path(get_config().tasks.base_path) / "tasks_data"
        self.storage = Storage(base_path)

    async def is_owner(self, task_id: int, user_id: int) -> bool:
        with self.db_session() as db:
            return (
                db.query(Task)
                .filter(
                    Task.task_id == task_id,
                    Task.user_id == user_id,
                )
                .first()
                != None
            )

    async def get_task(self, task_id) -> Task:
        with self.db_session() as db:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            return task

    async def get_full_task(self, task_id: int) -> FullTask:
        task = await self.get_task(task_id)
        if task is None:
            return None
        with self.db_session() as db:
            task = db.query(Task).filter(Task.task_id == task_id).first()
        if task is None:
            return None
        path = await self.storage.get_file_path(Path(str(task_id)) / "task.yaml")
        try:
            task_spec = TaskSpec.from_yaml(path)
            return FullTask.get(task, task_spec)
        except Exception as e:
            full_task = FullTask.partial(task)
            full_task.status = "corrupted"
            return full_task

    async def list_full_tasks(self) -> List[FullTask]:
        tasks = await self.list_tasks()
        full_tasks = [await self.get_full_task(t.task_id) for t in tasks]
        return full_tasks

    async def get_image_path(self, task_id: int, image_name: str):
        return await self.storage.get_file_path(Path(str(task_id)) / image_name)

    async def list_tasks(self) -> List[Task]:
        with self.db_session() as db:
            tasks = db.query(Task).all()
            return tasks

    async def save(self, task_id: int, image_name: str, data: Dict) -> None:
        self.storage.save_as_json(f"{Path(str(task_id)) / image_name}.json", data)

    async def delete(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.db_session() as db:
            db.query(Annotation).filter(Annotation.task_id == task_id).delete()
            db.query(Task).filter(Task.task_id == task_id).delete()
            db.commit()

        await self.storage.delete_folder(str(task_id))
