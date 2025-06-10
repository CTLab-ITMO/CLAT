import os
import shutil
from pathlib import Path
from typing import Tuple, Dict, List

from .config import LocalStorageConfig, StorageConfig, Config
from .utils import Singleton


class Storage(object):
    __code: str = 'default'
    __root: Path = None
    __is_time_based: bool = False
    __df_path: Path = None
    __vote_number: int = 3

    def __init__(self, config: StorageConfig) -> None:
        super().__init__()
        self.__code = config.code
        if hasattr(config, 'vote_number'):
            self.__vote_number = int(config.vote_number)
        if hasattr(config, 'path'):
            self.__root = Path(config.path)
        if hasattr(config, 'df_path'):
            self.__df_path = Path(config.df_path)

    def to_path(self, path: str | Path = None, name: str = None) -> Path:
        raise NotImplementedError()

    def move(self, from_path: str | Path, from_name: str, to_path: str | Path, to_name: str) -> Tuple[str, str, str]:
        raise NotImplementedError()

    def files(self, exts: List[str] = None, folder: Path = None) -> List[Tuple[str, str, str]]:
        raise NotImplementedError()

    def move_to(self, from_path: str | Path, from_name: str, to_path: str | Path, to_name: str) -> Tuple[str, str, str]:
        raise NotImplementedError()

    def copy_to(self, from_path: str | Path, from_name: str, to_path: str | Path, to_name: str) -> Tuple[str, str, str]:
        raise NotImplementedError()

    def remove(self, path: str | Path, name: str) -> None:
        raise NotImplementedError()

    @property
    def vote_number(self) -> int:
        return self.__vote_number
    @property
    def code(self) -> str:
        return self.__code

    @property
    def root(self) -> Path:
        return self.__root

    @property
    def is_time_based(self) -> bool:
        return self.__is_time_based

    @property
    def df_path(self) -> Path:
        return self.df_path


class LocalStorage(Storage):

    def __init__(self, config: LocalStorageConfig) -> None:
        super().__init__(config)

    def move_to(self, from_path: str | Path, from_name: str, to_path: str | Path, to_name: str) -> Tuple[str, str, str]:
        if not to_path.exists():
            os.makedirs(to_path)
        shutil.move(
            str(Path(self.root, from_path, from_name)),
            str(Path(to_path, to_name))
        )

        return self.code, str(to_path), to_name

    def move(self, from_path: str | Path, from_name: str, to_path: str | Path, to_name: str) -> Tuple[str, str, str]:
        to_path = Path(self.root, to_path)
        if not to_path.exists():
            os.makedirs(to_path)
        shutil.move(
            str(Path(self.root, from_path, from_name)),
            str(Path(to_path, to_name))
        )
        return self.code, str(to_path), to_name

    def files(self, exts: List[str] = None, folder: Path = None) -> List[Tuple[str, str, str]]:
        p = self.root if folder is None else Path(self.root, folder)
        files = []

        def to_tuple(f: Path) -> Tuple[str, str, str]:
            return self.code, str(folder) if folder is not None else '/', str(f.name)

        if exts is not None and len(exts) > 0:
            for ext in exts:
                files.extend([to_tuple(f) for f in Path(p).glob(ext)])
        else:
            files.extend([to_tuple(f) for f in p.iterdir() if f.is_file()])
        return files

    def to_path(self, path: str | Path = None, name: str = None) -> Path:
        p = self.root
        if path is not None and str(path) != '/':
            p = Path(p, path)
        if name is not None:
            p = Path(p, name)
        return p

    def copy_to(self, from_path: str | Path, from_name: str, to_path: str | Path, to_name: str) -> Tuple[str, str, str]:
        if not to_path.exists():
            os.makedirs(to_path)
        shutil.copy(
            str(Path(self.root, from_path, from_name)),
            str(Path(to_path, to_name))
        )
        return self.code, str(to_path), to_name

    def remove(self, path: str | Path, name: str) -> None:
        os.remove(str(Path(self.root, path, name)))
        return

    def walkdir(self, exts=['.jpg', '.png', '.jpeg']) -> List[Tuple[str, str, str]]:
        data = []
        # Traverse the directory tree starting from 'folder'.
        for root, dirs, files in os.walk(self.root, topdown=True):

            # Check if the file extension is in the allowed 'file_types'.
            for file in files:
                if os.path.splitext(file)[1] not in exts:
                    continue  # Skip the file if the extension is not in 'file_types'.

                # Yield the current directory path and the filename that matches criteria.
                c, rec_f, file = self.code, root.replace(str(self.root), "")[1:], str(file)
                if rec_f == "":
                    rec_f = "/"

                data.append((c, rec_f, file))

        return data



class StorageFactory(object):
    @staticmethod
    def get_storage(storage_cfg: StorageConfig) -> Storage:
        if isinstance(storage_cfg, LocalStorageConfig):
            return LocalStorage(storage_cfg)
        return Storage(storage_cfg)


class Storages(Singleton):
    __storages: Dict[str, Storage] = {}

    def get(self, code: str = 'default'):
        if code not in self.__storages:
            storage_cfg = Config.get_instance().storages.storage(code)
            if storage_cfg is None:
                raise RuntimeError(f'Unknown storage with code [{code}]')
            self.__storages[code] = StorageFactory.get_storage(storage_cfg)
        return self.__storages[code]


storages = Storages()