import numpy as np
import pytest
from image_assessment_service.core.aggregation.aggregator import AnnotationAggregator
from image_assessment_service.core.aggregation.models import BBox


class TestAnnotationAggregator:
    @pytest.fixture
    def sample_bboxes(self):
        return [
            BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50])),
            BBox(id=2, label="cat", coords=np.array([12, 12, 52, 52])),
            BBox(id=3, label="cat", coords=np.array([14, 14, 54, 54])),
            BBox(id=4, label="dog", coords=np.array([100, 100, 150, 150])),
            BBox(id=5, label="dog", coords=np.array([102, 102, 152, 152])),
        ]

    def test_aggregation_all_labels(self, sample_bboxes):
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        result = aggregator.aggregate(sample_bboxes)

        assert len(result) == 2  # One for cats, one for dogs
        assert all(ann.type == "bbox" for ann in result)
        assert {ann.label for ann in result} == {"cat", "dog"}

        # Check coords are averaged properly
        cat_ann = next(ann for ann in result if ann.label == "cat")
        expected_cat_coords = np.mean([b.coords for b in sample_bboxes[:3]], axis=0)
        np.testing.assert_allclose(cat_ann.coords, expected_cat_coords)

    def test_aggregation_no_clusters(self):
        bboxes = [
            BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50])),
            BBox(id=2, label="dog", coords=np.array([100, 100, 150, 150])),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        assert len(aggregator.aggregate(bboxes)) == 0  # No clusters formed

    def test_aggregation_empty_input(self):
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        assert aggregator.aggregate([]) == []

    def test_aggregation_single_input(self):
        bbox = BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50]))
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        assert aggregator.aggregate([bbox]) == []

    def test_aggregation_mixed_labels_in_cluster(self):
        # Shouldn't happen with proper IoU threshold, but test robustness
        bboxes = [
            BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50])),
            BBox(
                id=2, label="dog", coords=np.array([12, 12, 52, 52])
            ),  # Same coords but different label
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.9, min_overlap=2)
        result = aggregator.aggregate(bboxes)
        # Should either ignore (no clusters) or take label from first item
        assert len(result) <= 1

    def test_min_overlap_one(self):
        bboxes = [
            BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50])),
            BBox(id=2, label="cat", coords=np.array([11, 11, 55, 55])),  # Пересекается
            BBox(id=3, label="cat", coords=np.array([60, 60, 100, 100])),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.3, min_overlap=1)
        result = aggregator.aggregate(bboxes)

        assert len(result) == 2  # Только cat кластер
        left = result[0].coords
        right = result[1].coords
        if left[0] > right[0]:
            left, right = right, left
        np.testing.assert_allclose(left, bboxes[0].coords, rtol=0.1)
        np.testing.assert_allclose(right, bboxes[2].coords)

    def test_partially_overlapping_bboxes(self):
        """Тест частично пересекающихся bbox с разными метками"""
        bboxes = [
            BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50])),
            BBox(id=2, label="cat", coords=np.array([30, 30, 70, 70])),  # Пересекается
            BBox(
                id=3, label="dog", coords=np.array([60, 60, 100, 100])
            ),  # Почти не пересекается
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.1, min_overlap=2)
        result = aggregator.aggregate(bboxes)

        assert len(result) == 1  # Только cat кластер
        assert result[0].label == "cat"

    def test_identical_bboxes_different_labels(self):
        """Тест полностью совпадающих bbox с разными метками"""
        bboxes = [
            BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50])),
            BBox(id=2, label="dog", coords=np.array([10, 10, 50, 50])),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.9, min_overlap=2)
        result = aggregator.aggregate(bboxes)
        assert len(result) == 0  # Не должны объединяться

    def test_zero_area_bboxes(self):
        """Тест вырожденных bbox с нулевой площадью"""
        bboxes = [
            BBox(
                id=1, label="cat", coords=np.array([10, 10, 10, 50])
            ),  # Нулевая ширина
            BBox(
                id=2, label="cat", coords=np.array([10, 10, 50, 10])
            ),  # Нулевая высота
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.1, min_overlap=2)
        result = aggregator.aggregate(bboxes)
        assert len(result) == 0  # Не должны образовывать кластер

    def test_floating_point_precision(self):
        """Тест на точность floating-point вычислений"""
        bboxes = [
            BBox(
                id=1,
                label="cat",
                coords=np.array([10.000001, 10.000001, 50.000001, 50.000001]),
            ),
            BBox(
                id=2,
                label="cat",
                coords=np.array([10.000002, 10.000002, 50.000002, 50.000002]),
            ),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.999999, min_overlap=2)
        result = aggregator.aggregate(bboxes)
        assert len(result) == 1  # Должны объединиться

    def test_large_coordinate_values(self):
        """Тест с очень большими значениями координат"""
        bboxes = [
            BBox(
                id=1,
                label="satellite",
                coords=np.array([100000, 100000, 100500, 100500]),
            ),
            BBox(
                id=2,
                label="satellite",
                coords=np.array([100100, 100100, 100600, 100600]),
            ),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.3, min_overlap=2)
        result = aggregator.aggregate(bboxes)
        assert len(result) == 1

    def test_multiple_clusters_same_label(self):
        """Тест с несколькими кластерами одинаковых меток"""
        bboxes = [
            # Кластер 1
            BBox(id=1, label="cat", coords=np.array([10, 10, 20, 20])),
            BBox(id=2, label="cat", coords=np.array([12, 12, 22, 22])),
            # Кластер 2
            BBox(id=3, label="cat", coords=np.array([100, 100, 110, 110])),
            BBox(id=4, label="cat", coords=np.array([102, 102, 112, 112])),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.4, min_overlap=2)
        result = aggregator.aggregate(bboxes)
        assert len(result) == 2  # Два отдельных кластера cat
