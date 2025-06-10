import pytest
from image_assessment_service.core.services.admin_service import AdminServiceImpl
from image_assessment_service.core.services.aggregation_service import (
    AggregationServiceImpl,
)
from image_assessment_service.core.services.annotation_service import (
    AnnotationServiceImpl,
)
from image_assessment_service.core.services.data_uploader_service import (
    DataUploaderServiceImpl,
)
from image_assessment_service.core.services.task_service import TaskServiceImpl


class _MockContainer:

    def __init__(self, db_session):
        self.admin_service = AdminServiceImpl(db_session)
        self.task_service = TaskServiceImpl(db_session)
        self.annotation_service = AnnotationServiceImpl(db_session)
        self.aggregation_service = AggregationServiceImpl(
            self.task_service, self.annotation_service, db_session
        )
        self.data_uploader_service = DataUploaderServiceImpl(db_session)

        print("Dependencies mock container inited")


@pytest.fixture
def mock_container(mock_config, db_session, monkeypatch):
    container = _MockContainer(db_session)

    monkeypatch.setattr("image_assessment_service.dependencies._instance", container)
