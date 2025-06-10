import numpy as np
from image_assessment_service.core.aggregation.models import BBox, Segmentation
from image_assessment_service.core.aggregation.utils import SimilarityCalculator


class TestSimilarityCalculator:
    def test_bbox_iou_identical(self):
        bbox1 = BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50]))
        bbox2 = BBox(id=2, label="cat", coords=np.array([10, 10, 50, 50]))
        assert SimilarityCalculator.calculate(bbox1, bbox2) == 1.0

    def test_bbox_iou_no_overlap(self):
        bbox1 = BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50]))
        bbox2 = BBox(id=2, label="cat", coords=np.array([60, 60, 100, 100]))
        assert SimilarityCalculator.calculate(bbox1, bbox2) == 0.0

    def test_bbox_iou_half_overlap(self):
        bbox1 = BBox(id=1, label="cat", coords=np.array([20, 30, 50, 60]))
        bbox2 = BBox(id=2, label="cat", coords=np.array([20, 40, 50, 70]))
        assert abs(SimilarityCalculator.calculate(bbox1, bbox2) - 0.5) < 0.000001

    def test_bbox_iou_partial_overlap(self):
        bbox1 = BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50]))
        bbox2 = BBox(id=2, label="cat", coords=np.array([30, 30, 70, 70]))
        iou = SimilarityCalculator.calculate(bbox1, bbox2)
        assert 0 < iou < 1

    def test_different_types_return_zero(self):
        bbox = BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50]))
        seg = Segmentation(id=1, label="cat")
        assert SimilarityCalculator.calculate(bbox, seg) == 0.0
