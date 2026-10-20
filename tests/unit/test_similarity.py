import numpy as np
from image_assessment_service.core.aggregation.models import BBox, Image, Segment
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
        seg = Segment(id=1, label="cat", points=np.array([10, 10, 50, 50]))
        assert SimilarityCalculator.calculate(bbox, seg) == 0.0

    def test_segment_iou_identical(self):
        points = np.array([10, 10, 50, 10, 50, 50, 10, 50])  # Квадрат
        seg1 = Segment(id=1, label="cat", points=points.copy())
        seg2 = Segment(id=2, label="cat", points=points.copy())
        assert SimilarityCalculator.calculate(seg1, seg2) == 1.0

    def test_segment_iou_no_overlap(self):
        seg1 = Segment(
            id=1, label="cat", points=np.array([10, 10, 50, 10, 50, 50, 10, 50])
        )
        seg2 = Segment(
            id=2, label="cat", points=np.array([60, 60, 100, 60, 100, 100, 60, 100])
        )
        assert SimilarityCalculator.calculate(seg1, seg2) == 0.0

    def test_segment_iou_half_overlap(self):
        # Первый полигон: квадрат [10, 10] - [50, 50]
        seg1 = Segment(
            id=1, label="cat", points=np.array([10, 10, 50, 10, 50, 50, 10, 50])
        )
        # Второй полигон: прямоугольник, перекрывающий половину первого по площади
        seg2 = Segment(
            id=2, label="cat", points=np.array([10, 30, 50, 30, 50, 70, 10, 70])
        )
        iou = SimilarityCalculator.calculate(seg1, seg2)
        assert (
            abs(iou - 0.333) < 0.001
        )  # Ожидается ~1/3 (площадь пересечения / объединения)

    def test_segment_iou_one_inside_other(self):
        # Внешний полигон
        seg1 = Segment(
            id=1, label="cat", points=np.array([0, 0, 100, 0, 100, 100, 0, 100])
        )
        # Внутренний полигон (25% площади от внешнего)
        seg2 = Segment(
            id=2, label="cat", points=np.array([25, 25, 75, 25, 75, 75, 25, 75])
        )
        iou = SimilarityCalculator.calculate(seg1, seg2)
        assert abs(iou - 0.25) < 0.001  # IoU = площадь внутреннего / площадь внешнего

    def test_segment_iou_touching_edges(self):
        seg1 = Segment(
            id=1, label="cat", points=np.array([10, 10, 50, 10, 50, 50, 10, 50])
        )
        seg2 = Segment(
            id=2, label="cat", points=np.array([50, 10, 90, 10, 90, 50, 50, 50])
        )
        assert SimilarityCalculator.calculate(seg1, seg2) == 0.0

    def test_segment_iou_invalid_polygon(self):
        seg1 = Segment(
            id=1, label="cat", points=np.array([10, 10, 50, 10, 50, 10, 10, 10])
        )  # Линия
        seg2 = Segment(
            id=2, label="cat", points=np.array([10, 10, 50, 10, 50, 50, 10, 50])
        )  # Квадрат
        assert SimilarityCalculator.calculate(seg1, seg2) == 0.0

    def test_segment_iou_inversed_order(self):
        seg1 = Segment(
            id=1, label="cat", points=np.array([50, 10, 90, 50, 50, 90, 10, 50])
        )
        seg2 = Segment(
            id=2, label="cat", points=np.array([10, 50, 50, 90, 90, 50, 50, 10])
        )
        iou = SimilarityCalculator.calculate(seg1, seg2)
        assert abs(iou - 1.0) < 0.001  # Пересечение есть, но не полное
