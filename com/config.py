from typing import Dict

import yaml
from pathlib import Path

from .utils import Singleton

class StorageConfig(object):
    __code: str = None

    def __init__(self, code: str, config_map: Dict = None) -> None:
        super().__init__()
        if config_map is None:
            self.__code = 'default'
            return
        self.__code = code
        if 'path' not in config_map and 'params' not in config_map:
            raise RuntimeError(f'Path for storage {code} is''t configured!')

    @property
    def code(self) -> str:
        return self.__code

class LocalStorageConfig(StorageConfig):
    __path: str = None

    def __init__(self, code: str, config_map: Dict = None) -> None:
        super().__init__(code, config_map)
        self.__path = config_map['path'] if 'path' in config_map else config_map['params']['path']

    @property
    def path(self) -> str:
        return self.__path

class Config(Singleton):
    __storages = None

    def load(self, yml_path: Path):
        config_map = None
        with open(str(yml_path), "r") as yml_stream:
            try:
                config_map = yaml.safe_load(yml_stream)
            except yaml.YAMLError as exc:
                raise RuntimeError(f'Error loading configuration file: {exc}')
        if config_map is None:
            raise RuntimeError('Configuration isn''t loaded!')

        self.__storages = LocalStorageConfig(config_map['storages'], path=config_map['storages']['mdc'])
    @property
    def storages(self) -> LocalStorageConfig:
        return self.__storages


config = Config()
