from typing import Dict

from com.utils import SingletonVec
from com.storage import Storage, LocalStorage, LocalStorageConfig
from image_assessment_service.config import get_config, LocalStorageConfig as lsg


class Storages(metaclass=SingletonVec):
    __storages: Dict[str, Storage] = {}

    def get(self, code: str):
        if code not in self.__storages:
            storage_cfg = get_config().storages[code]
            if not isinstance(storage_cfg, lsg):
                raise RuntimeError(f'Unsupported storage type with code [{code}]')
            cfg = LocalStorageConfig(storage_cfg.code, {'path':storage_cfg.path})
            self.__storages[code] = LocalStorage(cfg)
        return self.__storages[code]
