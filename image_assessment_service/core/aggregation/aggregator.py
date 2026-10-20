from typing import Dict, List

from image_assessment_service.core.aggregation.dbscan import DBSCANClustering
from image_assessment_service.core.aggregation.models import Annotation, Image
from image_assessment_service.core.aggregation.utils import SimilarityCalculator


class AnnotationAggregator:
    def __init__(self, threshold_iou: float = 0.5, min_overlap: int = 2):
        self.threshold_iou = threshold_iou
        self.min_overlap = min_overlap

    def aggregate(self, annotations: List[Annotation]) -> List[Annotation]:
        if not annotations:
            return []

        type_groups = self._group_by_type(annotations)

        aggregated = []
        for ann_type, group in type_groups.items():
            if ann_type in ("bbox", "segment"):
                aggregated.extend(self._aggregate_spatial(group))
            elif ann_type == "image":
                aggregated.extend(self._aggregate_images(group))

        return aggregated

    def _aggregate_spatial(self, annotations: List[Annotation]) -> List[Annotation]:
        """Общий метод для агрегации bbox и сегментов."""
        if not annotations:
            return []

        dbscan = DBSCANClustering(eps=self.threshold_iou, min_samples=self.min_overlap)
        clusters = dbscan.cluster(annotations)

        aggregated = []
        for cluster_id, cluster in enumerate(clusters):
            best_ann = self._select_best_annotation(cluster)
            if best_ann is None:
                continue

            best_ann.id = cluster_id
            aggregated.append(best_ann)

        return aggregated

    def _aggregate_images(self, images: List[Annotation]) -> List[Annotation]:
        if not images:
            return []

        label_counts = _count_labels(images)

        main_label = max(label_counts, key=label_counts.get, default=None)
        return [Image(id=0, label=main_label)] if main_label else []

    def _group_by_type(self, annotations: List[Annotation]) -> Dict[str, List[Annotation]]:
        type_groups = {}
        for ann in annotations:
            ann_type = ann.type
            if ann_type not in type_groups:
                type_groups[ann_type] = []
            type_groups[ann_type].append(ann)

        return type_groups

    def _select_best_annotation(self, cluster: List[Annotation]):
        if not cluster:
            return None

        main_label = self._get_main_label(cluster)
        if not main_label:
            return None

        filtered_cluster = [c for c in cluster if c.label == main_label]

        return max(
            filtered_cluster,
            key=lambda x: sum(
                SimilarityCalculator.calculate(x, y)
                for y in filtered_cluster
                if y != x
            ),
        )

    def _get_main_label(self, cluster: List[Annotation]) -> str | None:
        label_counts = _count_labels(cluster)

        main_label = max(label_counts, key=label_counts.get, default=None)
        return main_label if label_counts[main_label] >= self.min_overlap else None


def _count_labels(annotations: List[Annotation]) -> Dict[str, int]:
    label_counts: Dict[str, int] = {}
    for ann in annotations:
        label_counts[ann.label] = label_counts.get(ann.label, 0) + 1

    return label_counts