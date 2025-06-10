from image_assessment_service.autorization.models.database import db_session
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


class _Container:

    def __init__(self):
        self.admin_service = AdminServiceImpl(db_session)
        self.task_service = TaskServiceImpl(db_session)
        self.annotation_service = AnnotationServiceImpl(db_session)
        self.aggregation_service = AggregationServiceImpl(
            self.task_service, self.annotation_service, db_session
        )
        self.data_uploader_service = DataUploaderServiceImpl(db_session)

        print("Dependencies container inited")


_instance = None


def get_container():
    global _instance
    if _instance is None:
        _instance = _Container()
    return _instance
