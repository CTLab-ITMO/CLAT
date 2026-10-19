import numpy as np
import pytest
from image_assessment_service.core.aggregation.aggregator import AnnotationAggregator
from image_assessment_service.core.aggregation.models import BBox, Image, Segment


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

    @pytest.fixture
    def sample_segments(self):
        return [
            Segment(
                id=1, label="cat", points=np.array([10, 10, 50, 10, 50, 50, 10, 50])
            ),
            Segment(
                id=2, label="cat", points=np.array([12, 12, 52, 12, 52, 52, 12, 52])
            ),
            Segment(
                id=3,
                label="dog",
                points=np.array([100, 100, 150, 100, 150, 150, 100, 150]),
            ),
            Segment(
                id=4,
                label="dog",
                points=np.array([102, 102, 152, 102, 152, 152, 102, 152]),
            ),
        ]

    @pytest.fixture
    def sample_images(self):
        return [
            Image(id=1, label="car"),
            Image(id=2, label="car"),
            Image(id=3, label="bike"),
            Image(id=4, label="bike"),
            Image(id=5, label="bike"),
        ]

    # Тесты для Segment
    def test_segment_aggregation_basic(self, sample_segments):
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        result = aggregator.aggregate(sample_segments)

        assert len(result) == 2  # Один кластер для cat, один для dog
        assert all(isinstance(ann, Segment) for ann in result)
        assert {ann.label for ann in result} == {"cat", "dog"}

    def test_segment_aggregation_no_overlap(self):
        segments = [
            Segment(
                id=1, label="cat", points=np.array([10, 10, 20, 10, 20, 20, 10, 20])
            ),
            Segment(
                id=2,
                label="cat",
                points=np.array([100, 100, 110, 100, 110, 110, 100, 110]),
            ),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        assert len(aggregator.aggregate(segments)) == 0

    def test_segment_aggregation_partial_overlap(self):
        segments = [
            Segment(
                id=1, label="cat", points=np.array([10, 10, 50, 10, 50, 50, 10, 50])
            ),
            Segment(
                id=2, label="cat", points=np.array([30, 30, 70, 30, 70, 70, 30, 70])
            ),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.1, min_overlap=2)
        result = aggregator.aggregate(segments)
        assert len(result) == 1
        assert result[0].label == "cat"

    def test_segment_aggregation_identical(self):
        points = np.array([10, 10, 50, 10, 50, 50, 10, 50])
        segments = [
            Segment(id=1, label="cat", points=points.copy()),
            Segment(id=2, label="cat", points=points.copy()),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        result = aggregator.aggregate(segments)
        assert len(result) == 1
        np.testing.assert_array_equal(result[0].points, points)

    def test_segment_aggregation_degenerate(self):
        segments = [
            Segment(
                id=1, label="cat", points=np.array([10, 10, 20, 10, 10, 10])
            ),  # Линия
            Segment(
                id=2, label="cat", points=np.array([10, 10, 10, 20, 10, 10])
            ),  # Линия
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        assert len(aggregator.aggregate(segments)) == 0

    # Тесты для Image
    def test_image_aggregation_basic(self, sample_images):
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        result = aggregator.aggregate(sample_images)

        assert len(result) == 1  # Только одна агрегированная метка
        assert isinstance(result[0], Image)
        assert result[0].label == "bike"  # bike встречается чаще

    def test_image_aggregation_tie(self):
        images = [
            Image(id=1, label="car"),
            Image(id=2, label="bike"),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        result = aggregator.aggregate(images)
        assert len(result) == 1
        assert result[0].label in {"car", "bike"}  # Любая из меток

    def test_image_aggregation_single(self):
        image = Image(id=1, label="car")
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        result = aggregator.aggregate([image])
        assert len(result) == 1
        assert result[0].label == "car"

    def test_image_aggregation_empty(self):
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        assert aggregator.aggregate([]) == []

    # Комбинированные тесты
    def test_mixed_annotation_types(self):
        annotations = [
            BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50])),
            BBox(id=2, label="cat", coords=np.array([12, 12, 52, 52])),
            Segment(
                id=3,
                label="dog",
                points=np.array([100, 100, 150, 100, 150, 150, 100, 150]),
            ),
            Segment(
                id=4,
                label="dog",
                points=np.array([102, 102, 152, 102, 152, 152, 102, 152]),
            ),
            Image(id=5, label="car"),
            Image(id=6, label="car"),
        ]
        aggregator = AnnotationAggregator(threshold_iou=0.5, min_overlap=2)
        result = aggregator.aggregate(annotations)

        assert len(result) == 3  # cat bbox, dog segment, car image
        assert sum(isinstance(ann, BBox) for ann in result) == 1
        assert sum(isinstance(ann, Segment) for ann in result) == 1
        assert sum(isinstance(ann, Image) for ann in result) == 1
