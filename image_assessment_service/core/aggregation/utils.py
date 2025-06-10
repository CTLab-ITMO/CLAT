from image_assessment_service.core.aggregation.models import (
    Annotation,
    BBox,
    Segmentation,
)


class SimilarityCalculator:

    @staticmethod
    def calculate(ann1: Annotation, ann2: Annotation) -> float:
        if ann1.type == "bbox" and ann2.type == "bbox":
            return SimilarityCalculator._bbox_iou(ann1, ann2)
        elif ann1.type == "segmentation" and ann2.type == "segmentation":
            return SimilarityCalculator._segmentation_iou(ann1, ann2)
        else:
            return 0.0  # Different types are not comparable

    @staticmethod
    def _bbox_iou(bbox1: BBox, bbox2: BBox) -> float:
        box1 = bbox1.coords
        box2 = bbox2.coords

        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    @staticmethod
    def _segmentation_iou(seg1: Segmentation, seg2: Segmentation) -> float:
        # Placeholder for segmentation IoU calculation
        # In real implementation, use polygon intersection or mask pixels
        return 0.0  # Implement this when adding segmentation support
