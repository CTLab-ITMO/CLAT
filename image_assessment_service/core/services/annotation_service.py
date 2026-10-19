import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from image_assessment_service.assessment.services.detection.service import DetectionService
from image_assessment_service.autorization.models.core import Annotation, Task, User
from image_assessment_service.config import get_config
from image_assessment_service.core.services.consts import TaskFileTypes
from image_assessment_service.core.storage import Storage


class AnnotationServiceImpl:
    def __init__(self, db_session):
        self.db_session = db_session
        self.base_path = Path(DetectionService().base_path) / "annotations_data"
        self.storage = Storage(self.base_path)

    async def get_task_annotations_with_users(self, task_id: int) -> List[Dict]:
        rows = await self._query_task_annotations(task_id)
        return [await self._build_annotation_info(r) for r in rows]

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
            _ensure_annotator_limit(db, task_id, task.annotators_count)

            new_annotation = self._build_annotation(task, user_id, description)
            db.add(new_annotation)
            db.commit()
            annotation_id = new_annotation.annotation_id

        await self._copy_drafts(task_id, annotation_id)

        return annotation_id

    async def get_annotation_status(self, task_id: int, user_id: int) -> dict:
        annotation = self._find_user_annotation(task_id, user_id)
        if annotation:
            return {"status": "in_progress", "annotation_id": annotation.annotation_id}

        return await self._get_available_status(task_id)

    async def export(
        self,
        annotation_id: int,
        export_format: str,
        include_bbox: bool,
        include_seg: bool,
        include_cls: bool,
        include_images: bool,
    ) -> Path:
        temp_file_path = await self._create_temp_export_file(annotation_id, export_format)
        annotation_folder = await self.storage.get_file_path(Path(str(annotation_id)))

        self._write_zip(temp_file_path, annotation_folder)

        return Path(temp_file_path)

    async def save(self, annotation_id: int, image_name: str, data: List) -> None:
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

    async def _query_task_annotations(self, task_id: int):
        with self.db_session() as db:
            return (
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

    async def _build_annotation_info(self, r) -> Dict:
        return {
            "id": r.annotation_id,
            "created_at": r.created_at,
            "deadline": r.deadline,
            "description": r.description,
            "status": r.status,
            "has_scores": (await self.get_scores_path(r.annotation_id)).exists(),
            "user": {"id": r.user_id, "nickname": r.nickname, "email": r.email},
        }

    def _build_annotation(self, task: Task, user_id: int, description) -> Annotation:
        return Annotation(
            task_id=task.task_id,
            user_id=user_id,
            status="in_progress",
            deadline=min(
                datetime.now() + timedelta(days=task.days_to_complete),
                task.deadline,
            ),
            description=description,
        )

    async def _copy_drafts(self, task_id: int, new_annotation_id: int) -> None:
        drafts = self.__get_all_drafts_indexed_by_image_name(task_id)
        for image_name, data in drafts.items():
            await self.save(new_annotation_id, image_name, data)

    def __get_all_drafts_indexed_by_image_name(self, task_id: int) -> dict:
        import json
        result = dict()
        drafts_dir = self.__tasks_path() / str(task_id) / TaskFileTypes.FILE_TYPE_SEGMENTATION_DRAFT
        for draft_path in drafts_dir.glob("*.json"):
            with open(draft_path, "r", encoding="utf-8") as f:
                img_file_name = draft_path.stem
                result[img_file_name] = json.load(f)
        return result

    def __tasks_path(self):
        return self.base_path / '..' / 'tasks_data'

    def _find_user_annotation(self, task_id: int, user_id: int):
        with self.db_session() as db:
            return (
                db.query(Annotation)
                .filter(Annotation.task_id == task_id, Annotation.user_id == user_id)
                .first()
            )

    async def _get_available_status(self, task_id: int) -> dict:
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

        return {
            "status": "unavailable",
            "annotators_limit": annotators_limit,
            "annotators_now": annotators_now,
        }

    async def _create_temp_export_file(self, annotation_id: int, export_format: str):
        tmp_file_name = f"{annotation_id}_{export_format}.zip"
        await self.storage.save(Path("export") / tmp_file_name, "")  # create file

        return await self.storage.get_file_path(
            Path("export") / tmp_file_name
        )

    def _write_zip(self, temp_file_path, annotation_folder) -> None:
        json_files = list(annotation_folder.glob("*.json"))

        with zipfile.ZipFile(temp_file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for json_file in json_files:
                zip_file.write(json_file, json_file.name)


def _ensure_annotator_limit(db, task_id: int, annotators_limit: int) -> None:
    annotators_now = (
        db.query(Annotation).filter(Annotation.task_id == task_id).count()
    )
    if annotators_now >= annotators_limit:
        raise HTTPException(400, "РЎР»РёС€РєРѕРј РјРЅРѕРіРѕ Р°РЅРЅРѕС‚Р°С‚РѕСЂРѕРІ")
