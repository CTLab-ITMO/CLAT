from typing import Dict

from com.utils import SingletonVec
from com.storage import LocalStorage, LocalStorageConfig, Storage


class Storages(metaclass=SingletonVec):
    __storages: Dict[str, Storage] = {}

    def get(self, code: str):
        if code not in self.__storages:
            from image_assessment_service.assessment.services.base import AssessmentService

            path = str(AssessmentService.resolve_path(code))
            cfg = LocalStorageConfig(code, {'path': path})
            self.__storages[code] = LocalStorage(cfg)
        return self.__storages[code]