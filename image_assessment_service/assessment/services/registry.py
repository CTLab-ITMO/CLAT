from typing import Dict, List, Optional, Type

from image_assessment_service.assessment.services.base import AssessmentService
from image_assessment_service.assessment.services.classification.service import ClassificationService
from image_assessment_service.assessment.services.detection.service import DetectionService
from image_assessment_service.assessment.services.segmentation.service import SegmentationService

SERVICES: Dict[str, Type] = {
    "detection": DetectionService,
    "segmentation": SegmentationService,
    "classification": ClassificationService,
}

_registry: Dict[str, AssessmentService] = {}


def register_services(services: List[AssessmentService]) -> None:
    _registry.clear()
    for service in services:
        _registry[service.code] = service


def get_feature(code: str) -> Optional[AssessmentService]:
    return _registry.get(code)


def get_features() -> List[AssessmentService]:
    return list(_registry.values())