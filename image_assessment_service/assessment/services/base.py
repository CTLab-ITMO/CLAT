from abc import ABC
from pathlib import Path

from image_assessment_service.config import get_config


class AssessmentService(ABC):
    """Базовый сервис разметки. Читает свой конфиг и резолвит путь через него."""

    code: str = ""

    def __init__(self):
        cfg = get_config().feature_config(self.code)
        if cfg is None:
            raise ValueError(f"Config for service/feature [{self.code}] is not found")
        self._cfg = cfg

    @classmethod
    def resolve_path(cls, code: str) -> Path:
        """Полный путь фичи/сервиса, берётся из конфига (не зависит от storages)."""
        cfg = get_config().feature_config(code)
        if cfg is None or not cfg.path:
            raise ValueError(f"Path for service/feature [{code}] is not configured")
        return Path(cfg.path)

    @property
    def storage_path(self) -> Path:
        return self.resolve_path(self.code)

    @property
    def enabled(self) -> bool:
        return self._cfg.enabled

    def init(self, db) -> None:
        """Инициализация сервиса. Для сервисов-контейнеров (detection/segmentation) — no-op,
        фичи оценки переопределяют и сканируют свои данные."""
        pass