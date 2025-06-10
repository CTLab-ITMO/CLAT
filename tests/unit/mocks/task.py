from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile
from image_assessment_service.dependencies import get_container


@pytest.fixture
def test_images_dir():
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def _task_metadata_1():
    deadline = (datetime.now() + timedelta(days=7)).isoformat()
    return {
        "title": "Test task",
        "deadline": deadline,
        "annotators_count": 123,
        "days_to_complete": 5,
        "description": "Test description",
        "num_images": 1,
        "bbox_labels": ["cat", "notacat"],
        "segmentation_labels": [],
        "image_names": ["image1.jpg"],
    }


@pytest.fixture
def mock_upload_file():
    """Фикстура для создания мока UploadFile"""

    def _create_upload_file(file_path: Path):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = file_path.name
        mock_file.read = AsyncMock(return_value=file_path.read_bytes())
        return mock_file

    return _create_upload_file


@pytest.fixture
async def create_test_task_1(_task_metadata_1, test_images_dir, mock_upload_file):
    user_id = 1

    task_id = await get_container().data_uploader_service.init_upload(
        metadata=_task_metadata_1, user_id=user_id
    )

    upload_file = mock_upload_file(test_images_dir / "image1.jpg")
    await get_container().data_uploader_service.upload_file(task_id, upload_file)

    await get_container().data_uploader_service.finish_upload(task_id)

    return task_id
