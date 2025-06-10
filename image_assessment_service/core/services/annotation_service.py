from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from image_assessment_service.autorization.models.core import Annotation, Task, User
from image_assessment_service.config import get_config
from image_assessment_service.core.storage import Storage


class AnnotationServiceImpl:
    def __init__(self, db_session):
        self.db_session = db_session
        base_path = Path(get_config().tasks.base_path) / "annotations_data"
        self.storage = Storage(base_path)

    async def get_task_annotations_with_users(self, task_id: int) -> List[Annotation]:
        req = None
        with self.db_session() as db:
            req = (
                db.query(
                    Annotation.annotation_id,
                    Annotation.created_at,
                    Annotation.deadline,
                    Annotation.description,
                    Annotation.status,
                    User.id.label("user_id"),
                    User.nickname,
                    User.email,
                )
                .join(User, Annotation.user_id == User.id)
                .filter(Annotation.task_id == task_id)
                .all()
            )
        return [
            {
                "id": r.annotation_id,
                "created_at": r.created_at,
                "deadline": r.deadline,
                "description": r.description,
                "status": r.status,
                "has_scores": (await self.get_scores_path(r.annotation_id)).exists(),
                "user": {"id": r.user_id, "nickname": r.nickname, "email": r.email},
            }
            for r in req
        ]

    async def get_task_annotations(self, task_id: int) -> List[Annotation]:
        with self.db_session() as db:
            return db.query(Annotation).filter(Annotation.task_id == task_id).all()

    async def get_annotations(self, user_id: int) -> List[Annotation]:
        with self.db_session() as db:
            return db.query(Annotation).filter(Annotation.user_id == user_id).all()

    async def is_owner(self, annotation_id: int, user_id: int) -> bool:
        with self.db_session() as db:
            return (
                db.query(Annotation)
                .filter(
                    Annotation.annotation_id == annotation_id,
                    Annotation.user_id == user_id,
                )
                .first()
                != None
            )

    async def get_annotation(self, annotation_id: int) -> Annotation:
        with self.db_session() as db:
            annotation = (
                db.query(Annotation)
                .filter(Annotation.annotation_id == annotation_id)
                .first()
            )
            return annotation

    async def create_annotation(
        self, task_id: int, user_id: int, description=None
    ) -> int:
        with self.db_session() as db:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            annotators_limit = task.annotators_count
            annotators_now = (
                db.query(Annotation).filter(Annotation.task_id == task_id).count()
            )
            if annotators_now < annotators_limit:
                new_annotation = Annotation(
                    task_id=task_id,
                    user_id=user_id,
                    status="in_progress",
                    deadline=min(
                        datetime.now() + timedelta(days=task.days_to_complete),
                        task.deadline,
                    ),
                    description=description,
                )
                db.add(new_annotation)
                db.commit()
                return new_annotation.annotation_id
            raise HTTPException(400, "Слишком много аннотаторов")

    async def get_annotation_status(self, task_id: int, user_id: int) -> str:
        annotation = None
        with self.db_session() as db:
            annotation = (
                db.query(Annotation)
                .filter(Annotation.task_id == task_id, Annotation.user_id == user_id)
                .first()
            )
        if annotation:
            return {"status": "in_progress", "annotation_id": annotation.annotation_id}
        if annotation is None:
            with self.db_session() as db:
                task = db.query(Task).filter(Task.task_id == task_id).first()
                annotators_limit = task.annotators_count
                annotators_now = (
                    db.query(Annotation).filter(Annotation.task_id == task_id).count()
                )
                if annotators_now < annotators_limit:
                    return {
                        "status": "available",
                        "annotators_limit": annotators_limit,
                        "annotators_now": annotators_now,
                    }
                else:
                    return {
                        "status": "unavailable",
                        "annotators_limit": annotators_limit,
                        "annotators_now": annotators_now,
                    }

    async def save(self, annotation_id: str, image_name: str, data: List) -> None:
        await self.storage.save_as_json(
            f"{Path(str(annotation_id)) / image_name}.json", data
        )

    async def get(self, annotation_id: str, image_name: str) -> List:
        ann = await self.storage.load_as_json(
            f"{Path(str(annotation_id)) / image_name}.json"
        )
        if ann is None:
            return []
        else:
            return ann

    async def delete(
        self, annotation_id: str, image_name: str
    ) -> Optional[Dict[str, Any]]:
        await self.storage.load(f"{Path(str(annotation_id)) / image_name}.json")

    async def delete_annotation(self, annotation_id: str) -> None:
        with self.db_session() as db:
            db.query(Annotation).filter(
                Annotation.annotation_id == annotation_id
            ).delete()
            db.commit()

        await self.storage.delete_folder(str(annotation_id))

    async def get_scores_path(self, annnotation_id: str) -> Path:
        return await self.storage.get_file_path(
            Path(str(annnotation_id)) / "scores.csv"
        )
