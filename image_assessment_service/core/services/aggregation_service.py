from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from scipy.optimize import linear_sum_assignment
import numpy as np

from image_assessment_service.autorization.models.core import Annotation, User
from image_assessment_service.core.aggregation.aggregator import AnnotationAggregator
from image_assessment_service.core.aggregation.models import (
    Annotation as AnnotationWrapper,
)
from image_assessment_service.core.aggregation.models import BBox, Image, Segment
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
        if not objects or not correct_objects:
            self.total_objects += len(objects)
            return

        sim_matrix = self._build_similarity_matrix(objects, correct_objects)
        self._count_correct_objects(sim_matrix, threshold_iou)
        self.total_objects += len(objects)

    def infer(self, total_correct_objects):
        self.macro_accuracy = self.correct_objects / (
            total_correct_objects + self.total_objects - self.correct_objects
        )
        self.micro_accuracy = self.sum_iou / (
            total_correct_objects + self.total_objects - self.correct_objects
        )

    def _build_similarity_matrix(self, objects: List[Annotation], correct_objects: List[Annotation]) -> np.ndarray:
        sim_matrix = np.zeros((len(objects), len(correct_objects)))

        for i, obj in enumerate(objects):
            for j, corr in enumerate(correct_objects):
                sim_matrix[i, j] = SimilarityCalculator.calculate(obj, corr)

        return sim_matrix

    def _count_correct_objects(self, sim_matrix: np.ndarray, threshold_iou: float) -> None:
        cost_matrix = 1 - sim_matrix

        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        for i, j in zip(row_ind, col_ind):
            score = sim_matrix[i, j]
            if score >= threshold_iou:
                self.correct_objects += 1
                self.sum_iou += score


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
        new_ann_id = await self._create_aggregated_annotation(annotations[0], full_task)

        agg = AnnotationAggregator(threshold_iou=threshold_iou, min_overlap=min_overlap)
        await self._aggregate_each_image(annotations, new_ann_id, full_task, agg)

        await self.calculate_scores(annotations, new_ann_id, full_task, threshold_iou)
        return new_ann_id

    async def calculate_scores(
        self,
        annotations: List[Annotation],
        target_ann_id: int,
        full_task,
        threshold_iou: float,
    ):
        scores, total_objs = await self._compute_scores(
            annotations, target_ann_id, full_task, threshold_iou
        )
        sorted_stats = self._finalize_scores(annotations, scores, total_objs)

        await self._write_scores_file(target_ann_id, sorted_stats, annotations)

    async def _create_aggregated_annotation(self, annotation: Annotation, full_task) -> int:
        return await self.annotation_service.create_annotation(
            annotation.task_id, full_task.user_id, description="Агрегация"
        )

    async def _aggregate_each_image(
        self,
        annotations: List[Annotation],
        new_ann_id: int,
        full_task,
        agg: AnnotationAggregator,
    ) -> None:
        for image_name in full_task.image_names:
            image_anns = await self._collect_image_annotations(annotations, image_name)

            res_image_anns = agg.aggregate(image_anns)
            if len(res_image_anns) > 0:
                await self.annotation_service.save(
                    new_ann_id,
                    image_name,
                    list(map(lambda x: x.to_dict(), res_image_anns)),
                )

    async def _collect_image_annotations(self, annotations: List[Annotation], image_name: str) -> List:
        image_anns = []
        for ann in annotations:
            user_anns = await self.annotation_service.get(
                ann.annotation_id, image_name
            )
            image_anns += self._raw_annotations_to_wrappers(
                ann.annotation_id, user_anns
            )

        return image_anns

    async def _compute_scores(self, annotations: List[Annotation], target_ann_id: int, full_task, threshold_iou: float):
        scores = {
            a.annotation_id: UserAnnotationStatistics(a.user_id) for a in annotations
        }
        total_target_annotation_objs = 0

        for image_name in full_task.image_names:
            target_objects = await self._load_annotation_objects(target_ann_id, image_name)
            total_target_annotation_objs += len(target_objects)

            await self._update_scores_for_image(
                scores, annotations, image_name, target_objects, threshold_iou
            )

        return scores, total_target_annotation_objs

    async def _update_scores_for_image(
        self,
        scores,
        annotations: List[Annotation],
        image_name: str,
        target_objects,
        threshold_iou: float,
    ) -> None:
        for ann in annotations:
            user_objects = await self._load_annotation_objects(ann.annotation_id, image_name)
            scores[ann.annotation_id].update(
                user_objects, target_objects, threshold_iou
            )

    async def _load_annotation_objects(self, annotation_id: int, image_name: str):
        return self._raw_annotations_to_wrappers(
            annotation_id,
            await self.annotation_service.get(annotation_id, image_name),
        )

    def _finalize_scores(self, annotations: List[Annotation], scores, total_objs: int):
        for ann in annotations:
            stats = scores[ann.annotation_id]
            stats.infer(total_objs)
            stats.user_id = ann.user_id

        return sorted(
            scores.values(), key=lambda x: (-x.macro_accuracy, -x.micro_accuracy)
        )

    async def _write_scores_file(self, target_ann_id: int, sorted_stats, annotations: List[Annotation]) -> None:
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
            if obj["type"] == "image":
                res.append(Image(annotation_id, obj["label"]))
            if obj["type"] == "segment":
                res.append(Segment(annotation_id, obj["label"], points=obj["points"]))
        return res