from pathlib import Path

from image_assessment_service.assessment.services.base import AssessmentService


class DetectionService(AssessmentService):
    """Сервис детекции: задания на разметку bbox. Определяет базовую папку заданий и аннотаций."""

    code = "detection"

    @property
    def base_path(self) -> Path:
        return self.storage_path