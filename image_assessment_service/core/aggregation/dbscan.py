from typing import List

import numpy as np
from image_assessment_service.core.aggregation.models import Annotation
from image_assessment_service.core.aggregation.utils import SimilarityCalculator
from sklearn.cluster import DBSCAN


class DBSCANClustering:
    def __init__(self, eps: float, min_samples: int):
        self.eps = eps
        self.min_samples = min_samples

    def cluster(self, annotations: List[Annotation]) -> List[List[Annotation]]:
        if len(annotations) == 0:
            return []

        n = len(annotations)
        dist_matrix = np.ones((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                sim = SimilarityCalculator.calculate(annotations[i], annotations[j])
                dist_matrix[i, j] = 1 - sim
                dist_matrix[j, i] = 1 - sim

        dbscan = DBSCAN(
            eps=1 - self.eps,
            min_samples=max(1, self.min_samples - 1),
            metric="precomputed",
        ).fit(dist_matrix)

        labels = dbscan.labels_
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

        res = [[] for _ in range(n_clusters_)]
        for ann, c in zip(annotations, labels):
            if c == -1:
                if self.min_samples == 1:
                    res.append([ann])
                # outlier
            else:
                res[c].append(ann)
        return res
