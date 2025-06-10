from dataclasses import dataclass

import numpy as np


@dataclass
class Annotation:
    id: int
    label: str
    type: str

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
        }


@dataclass(kw_only=True)
class BBox(Annotation):
    type: str = "bbox"
    coords: np.ndarray  # [x1, y1, x2, y2]

    def to_dict(self):
        base_dict = super().to_dict()
        return {**base_dict, "coords": self.coords}


@dataclass(kw_only=True)
class Segmentation(Annotation):
    type: str = "segmentation"
