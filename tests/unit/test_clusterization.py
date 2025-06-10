import numpy as np
import pytest
from image_assessment_service.core.aggregation.dbscan import DBSCANClustering
from image_assessment_service.core.aggregation.models import BBox


class TestDBSCANClustering:
    @pytest.fixture
    def sample_bboxes(self):
        return [
            BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50])),
            BBox(id=2, label="cat", coords=np.array([12, 12, 52, 52])),  # Similar to 1
            BBox(id=3, label="dog", coords=np.array([100, 100, 150, 150])),  # Different
            BBox(
                id=4, label="cat", coords=np.array([15, 15, 55, 55])
            ),  # Similar to 1 and 2
            BBox(
                id=5, label="dog", coords=np.array([105, 105, 155, 155])
            ),  # Similar to 3
        ]

    def test_clustering_with_min_overlap_2(self, sample_bboxes):
        dbscan = DBSCANClustering(eps=0.5, min_samples=2)
        clusters = dbscan.cluster(sample_bboxes)
        assert len(clusters) == 2
        clusters = sorted(clusters, key=lambda c: len(c))
        assert set([c.id for c in clusters[0]]) == {3, 5}
        assert set([c.id for c in clusters[1]]) == {1, 2, 4}

    def test_clustering_with_min_overlap_3(self, sample_bboxes):
        dbscan = DBSCANClustering(eps=0.5, min_samples=3)
        clusters = dbscan.cluster(sample_bboxes)
        assert len(clusters) == 1
        assert set([c.id for c in clusters[0]]) == {1, 2, 4}

    def test_empty_input(self):
        dbscan = DBSCANClustering(eps=0.5, min_samples=2)
        assert dbscan.cluster([]) == []

    def test_single_input(self):
        bbox = BBox(id=1, label="cat", coords=np.array([10, 10, 50, 50]))
        dbscan = DBSCANClustering(eps=0.5, min_samples=2)
        assert dbscan.cluster([bbox]) == []
