from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from image_assessment_service.autorization.models.core import Annotation, User
from image_assessment_service.core.aggregation.aggregator import AnnotationAggregator
from image_assessment_service.core.aggregation.models import (
    Annotation as AnnotationWrapper,
)
from image_assessment_service.core.aggregation.models import BBox
from image_assessment_service.core.aggregation.utils import SimilarityCalculator


@dataclass
class UserAnnotationStatistics:
    user_id: int
    correct_objects: int = 0
    total_objects: int = 0
    sum_iou: float = 0.0

    macro_accuracy: float = None
    micro_accuracy: float = None

    def update(
        self,
        objects: List[Annotation],
        correct_objects: List[Annotation],
        threshold_iou: float,
    ):
        for obj in objects:
            for correct_obj in correct_objects:
                obj_score = SimilarityCalculator.calculate(obj, correct_obj)
                if obj_score >= threshold_iou:
                    self.correct_objects += 1
                    self.sum_iou += obj_score
                    break
        self.total_objects += len(objects)

    def infer(self, total_correct_objects):
        self.macro_accuracy = self.correct_objects / (
            total_correct_objects + self.total_objects - self.correct_objects
        )
        self.micro_accuracy = self.sum_iou / (
            total_correct_objects + self.total_objects - self.correct_objects
        )


async def dump_scores_into_file(
    file_path: Path,
    stats_list: List[UserAnnotationStatistics],
    users_info: Dict[int, Dict],
):
    with open(file_path, "w") as f:
        f.write("id,nickname,email,macro_accuracy,micro_accuracy\n")
        for stats in stats_list:
            nickname = users_info[stats.user_id]["nickname"]
            email = users_info[stats.user_id]["email"]
            f.write(
                f"{stats.user_id},{nickname},{email},{stats.macro_accuracy},{stats.micro_accuracy}\n"
            )


async def get_users_info(db_session, user_ids: List[int]):
    with db_session() as db:
        users = (
            db.query(User.id, User.email, User.nickname)
            .filter(User.id.in_(user_ids))
            .all()
        )

        return {
            user.id: {"email": user.email, "nickname": user.nickname} for user in users
        }


class AggregationServiceImpl:
    def __init__(self, task_service, annotation_service, db_session):
        self.task_service = task_service
        self.annotation_service = annotation_service
        self.db_session = db_session

    async def aggregate_annotations(
        self,
        annotations: List[Annotation],
        threshold_iou: float,
        min_overlap: int,
    ) -> int:

        full_task = await self.task_service.get_full_task(annotations[0].task_id)
        new_ann_id = await self.annotation_service.create_annotation(
            annotations[0].task_id, full_task.user_id, description="Агрегация"
        )
        agg = AnnotationAggregator(threshold_iou=threshold_iou, min_overlap=min_overlap)
        image_names = full_task.image_names

        for image_name in image_names:
            image_anns = []
            for ann in annotations:
                user_anns = await self.annotation_service.get(
                    ann.annotation_id, image_name
                )
                wrapped = self._raw_annotations_to_wrappers(
                    ann.annotation_id, user_anns
                )
                image_anns += wrapped

            res_image_anns = agg.aggregate(image_anns)
            if len(res_image_anns) > 0:
                await self.annotation_service.save(
                    new_ann_id,
                    image_name,
                    list(map(lambda x: x.to_dict(), res_image_anns)),
                )

        await self.calculate_scores(annotations, new_ann_id, full_task, threshold_iou)
        return new_ann_id

    async def calculate_scores(
        self,
        annotations: List[Annotation],
        target_ann_id: int,
        full_task,
        threshold_iou: float,
    ):
        image_names = full_task.image_names

        scores = {
            a.annotation_id: UserAnnotationStatistics(a.user_id) for a in annotations
        }

        total_target_annotation_objs = 0

        for image_name in image_names:
            target_objects = self._raw_annotations_to_wrappers(
                target_ann_id,
                await self.annotation_service.get(target_ann_id, image_name),
            )
            total_target_annotation_objs += len(target_objects)

            for ann in annotations:
                user_objects = self._raw_annotations_to_wrappers(
                    ann.annotation_id,
                    await self.annotation_service.get(ann.annotation_id, image_name),
                )

                scores[ann.annotation_id].update(
                    user_objects, target_objects, threshold_iou
                )

        for ann in annotations:
            stats = scores[ann.annotation_id]
            stats.infer(total_target_annotation_objs)
            stats.user_id = ann.user_id

        sorted_stats = sorted(
            scores.values(), key=lambda x: (-x.macro_accuracy, -x.micro_accuracy)
        )

        users_info = await get_users_info(
            self.db_session, [ann.user_id for ann in annotations]
        )
        scores_file_path = await self.annotation_service.get_scores_path(target_ann_id)
        await dump_scores_into_file(scores_file_path, sorted_stats, users_info)

    def _raw_annotations_to_wrappers(
        self, annotation_id: int, annotations: List
    ) -> List[AnnotationWrapper]:
        res = []
        for obj in annotations:
            if obj["type"] == "bbox":
                res.append(BBox(annotation_id, obj["label"], coords=obj["coords"]))
        return res
