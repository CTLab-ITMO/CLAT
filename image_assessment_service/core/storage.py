import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Dict

import aiofiles


class Storage:
    def __init__(self, base_path: Path | str, max_open_files=100):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._file_locks: Dict[str, asyncio.Lock] = {}
        self._file_semaphore = asyncio.Semaphore(max_open_files)

    async def _get_lock(self, task_id: str) -> asyncio.Lock:
        """Получаем лок для конкретного файла (создаем при необходимости)"""
        task_id = str(task_id)
        async with self._lock:
            if task_id not in self._file_locks:
                self._file_locks[task_id] = asyncio.Lock()
            return self._file_locks[task_id]

    async def save(self, path: Path | str, data: str) -> None:
        """
        Асинхронно сохраняет данные в файл.
        Гарантирует, что параллельные запросы к одному файлу не конфликтуют.
        """
        lock = await self._get_lock(path)
        real_path = self.base_path / path

        async with lock:  # Блокируем доступ только к этому файлу
            real_path.parent.mkdir(parents=True, exist_ok=True)
            async with self._file_semaphore:
                async with aiofiles.open(real_path, mode="w", encoding="utf-8") as f:
                    await f.write(data)

    async def load(self, path: Path | str) -> str:
        lock = await self._get_lock(path)
        real_path = self.base_path / path

        async with lock:  # Блокируем доступ только к этому файлу
            if not real_path.exists():
                return None
            async with self._file_semaphore:
                async with aiofiles.open(real_path, mode="r", encoding="utf-8") as f:
                    return await f.read()

    async def delete(self, path: Path | str) -> None:
        lock = await self._get_lock(path)

        async with lock:  # Блокируем доступ только к этому файлу
            os.remove(str(path))

    async def delete_folder(self, folder_path: Path | str) -> None:
        async with self._lock:  # Берем глобальный лок
            shutil.rmtree(self.base_path / folder_path, ignore_errors=True)

    async def save_as_json(self, path: Path | str, data: str) -> None:
        await self.save(path, json.dumps(data, ensure_ascii=False, indent=2))

    async def load_as_json(self, path: Path | str):
        data = await self.load(path)
        if data is None:
            return None
        else:
            try:
                return json.loads(data)
            except Exception:
                return None

    async def get_file_path(self, path: Path | str) -> Path:
        return self.base_path / path
