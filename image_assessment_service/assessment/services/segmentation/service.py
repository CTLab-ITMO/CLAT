from pathlib import Path

from image_assessment_service.assessment.services.base import AssessmentService


class SegmentationService(AssessmentService):
    """Сервис сегментации: задания на разметку сегментов. Определяет базовую папку заданий и аннотаций."""

    code = "segmentation"

    @property
    def base_path(self) -> Path:
        return self.storage_path