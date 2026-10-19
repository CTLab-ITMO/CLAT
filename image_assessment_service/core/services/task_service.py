import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from image_assessment_service.assessment.services.detection.service import DetectionService
from image_assessment_service.autorization.models.core import Annotation, Task
from image_assessment_service.config import get_config
from image_assessment_service.core.services.consts import TaskFileTypes
from image_assessment_service.core.storage import Storage


@dataclass
class Attribute:
    key: str
    type: str
    options: List[str]

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "key": self.key,
            "type": self.type,
        }
        if self.options:
            data["options"] = self.options
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> None:
        return cls(
            key=data["key"],
            type=data["type"],
            options=data.get("options") or [],
        )


@dataclass
class TaskSpec:
    title: int
    description: str
    num_images: int
    bbox_labels: List[str]
    segmentation_labels: List[str]
    image_labels: List[str]
    attributes: List[Attribute]
    image_names: List[str]
    instructions: str

    def to_dict(self) -> Dict[str, Any]:
        """РљРѕРЅРІРµСЂС‚РёСЂСѓРµС‚ РѕР±СЉРµРєС‚ Task РІ СЃР»РѕРІР°СЂСЊ"""
        data = {
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "num_images": self.num_images,
        }
        if self.bbox_labels:
            data["bbox_labels"] = self.bbox_labels
        if self.segmentation_labels:
            data["segmentation_labels"] = self.segmentation_labels
        if self.image_labels:
            data["image_labels"] = self.image_labels
        if self.attributes:
            data["attributes"] = [a.to_dict() for a in self.attributes]
        if self.image_names:
            data["image_names"] = self.image_names
        return data

    def save_to_yaml(self, output_file: str) -> None:
        """РЎРѕС…СЂР°РЅСЏРµС‚ Р·Р°РґР°С‡Сѓ РІ YAML С„Р°Р№Р»"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskSpec":
        attributes = []
        if data.get("attributes"):
            attributes = [Attribute.from_dict(a) for a in data["attributes"]]
        """РЎРѕР·РґР°РµС‚ РѕР±СЉРµРєС‚ TaskSpec РёР· СЃР»РѕРІР°СЂСЏ"""
        return cls(
            title=data["title"],
            description=data["description"],
            num_images=data["num_images"],
            bbox_labels=data.get("bbox_labels") or [],
            segmentation_labels=data.get("segmentation_labels") or [],
            image_labels=data.get("image_labels") or [],
            attributes=attributes,
            image_names=data.get("image_names") or [],
            instructions=data["instructions"],
        )

    @classmethod
    def from_yaml(cls, input_file: str) -> "TaskSpec":
        """Р—Р°РіСЂСѓР¶Р°РµС‚ Р·Р°РґР°С‡Сѓ РёР· YAML С„Р°Р№Р»Р°"""
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return cls.from_dict(data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Р¤Р°Р№Р» {input_file} РЅРµ РЅР°Р№РґРµРЅ")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"РћС€РёР±РєР° РїСЂРё С‡С‚РµРЅРёРё YAML: {e}")
        except KeyError as e:
            raise ValueError(f"РћС‚СЃСѓС‚СЃС‚РІСѓРµС‚ РѕР±СЏР·Р°С‚РµР»СЊРЅРѕРµ РїРѕР»Рµ: {e}")


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
    image_labels: Optional[List[str]] = None
    attributes: Optional[List[Attribute]] = None
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
        base_path = Path(DetectionService().base_path) / "tasks_data"
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
        path = await self.storage.get_file_path(Path(str(task_id)) / TaskFileTypes.FILE_TYPE_SETTINGS / "task.yaml")
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
        return await self.storage.get_file_path(Path(str(task_id)) / TaskFileTypes.FILE_TYPE_IMAGE / image_name)

    async def list_tasks(self) -> List[Task]:
        with self.db_session() as db:
            tasks = db.query(Task).all()
            return tasks

    async def save(self, task_id: int, image_name: str, data: Dict) -> None:
        raise Exception("Unsupported")

    async def delete(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.db_session() as db:
            db.query(Annotation).filter(Annotation.task_id == task_id).delete()
            db.query(Task).filter(Task.task_id == task_id).delete()
            db.commit()

        await self.storage.delete_folder(str(task_id))

