from typing import List

import numpy as np
from image_assessment_service.core.aggregation.dbscan import DBSCANClustering
from image_assessment_service.core.aggregation.models import (
    Annotation,
    BBox,
    Segmentation,
)


class AnnotationAggregator:
    def __init__(self, threshold_iou: float = 0.5, min_overlap: int = 2):
        self.threshold_iou = threshold_iou
        self.min_overlap = min_overlap

    def aggregate(self, annotations: List[Annotation]) -> List[Annotation]:
        if not annotations:
            return []

        # Cluster similar annotations
        dbscan = DBSCANClustering(eps=self.threshold_iou, min_samples=self.min_overlap)
        clusters = dbscan.cluster(annotations)

        # Create consensus annotations
        aggregated = []
        for cluster_id, cluster in enumerate(clusters):
            if not cluster:
                continue

            labels = {}
            for ann in cluster:
                if ann.label not in labels:
                    labels[ann.label] = 1
                else:
                    labels[ann.label] += 1

            main_label = None
            main_label_cnt = -1
            for k, v in labels.items():
                if main_label_cnt < v:
                    main_label = k
                    main_label_cnt = v

            if main_label_cnt < self.min_overlap:
                continue

            if main_label_cnt < len(cluster):
                cluster = [c for c in cluster if c.label == main_label]

            # Create new consensus annotation
            if isinstance(cluster[0], BBox):
                new_ann = self._aggregate_bbox_cluster(cluster, cluster_id)
            elif isinstance(cluster[0], Segmentation):
                new_ann = self._aggregate_segmentation_cluster(cluster, cluster_id)
            else:
                continue

            aggregated.append(new_ann)

        return aggregated

    def _aggregate_bbox_cluster(self, cluster: List[BBox], new_id: int) -> BBox:
        avg_coords = np.mean([bbox.coords for bbox in cluster], axis=0).tolist()
        return BBox(id=new_id, label=cluster[0].label, coords=avg_coords)

    def _aggregate_segmentation_cluster(
        self, cluster: List[Segmentation], new_id: int
    ) -> Segmentation:
        # TODO: Implement segmentation aggregation
        return Segmentation(
            id=new_id,
            label=cluster[0].label,
            coords=cluster[0].coords,
        )
