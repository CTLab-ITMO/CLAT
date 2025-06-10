from datetime import datetime, timedelta
from typing import Dict, List

import pytest
from image_assessment_service.dependencies import get_container


@pytest.fixture
def valid_metadata():
    deadline = (datetime.now() + timedelta(days=7)).isoformat()
    return {
        "title": "Test task",
        "deadline": deadline,
        "annotators_count": 123,
        "days_to_complete": 5,
        "description": "Test description",
        "num_images": 4,
        "bbox_labels": ["cat", "notacat"],
        "segmentation_labels": [],
    }


@pytest.fixture
def create_test_annotation():
    async def inner(
        task_id: int = None,
        user_id: int = None,
        image_name_to_data: Dict[str, List] = {},
    ):
        annotation_id = await get_container().annotation_service.create_annotation(
            task_id, user_id
        )

        for image_name, data in image_name_to_data.items():
            await get_container().annotation_service.save(
                annotation_id, image_name, data
            )
        return annotation_id

    return inner


@pytest.fixture
def annotation_data_1():
    return [
        {"id": 1, "label": "cat", "type": "bbox", "coords": [10, 20, 30, 40]},
        {"id": 2, "label": "cat", "type": "bbox", "coords": [50, 60, 70, 80]},
    ]


@pytest.fixture
def annotation_data_2():
    return [
        {"id": 1, "label": "cat", "type": "bbox", "coords": [12, 20, 32, 40]},
    ]
