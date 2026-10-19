from typing import Dict, List, Optional, Type

from image_assessment_service.assessment.services.classification.features.aesth_assessment import (
    AesthAssessmentFeature,
)
from image_assessment_service.assessment.services.classification.features.base import AssessmentFeature
from image_assessment_service.assessment.services.classification.features.filter import ImageFilterFeature
from image_assessment_service.assessment.services.classification.features.reference_classification import (
    ReferenceClassificationFeature,
)
from image_assessment_service.assessment.services.classification.features.tech_assessment import (
    TechAssessmentFeature,
)
from image_assessment_service.config import get_config

CLASSIFICATION_FEATURES: Dict[str, Type[AssessmentFeature]] = {
    "tech": TechAssessmentFeature,
    "aesth": AesthAssessmentFeature,
    "filter": ImageFilterFeature,
    "classify": ReferenceClassificationFeature,
}


class ClassificationService:
    """Сервис классификации: группирует фичи оценки изображений (tech/aesth/filter/classify)."""

    code = "classification"
    features = CLASSIFICATION_FEATURES

    def build_features(self, feature_codes: Optional[List[str]] = None) -> List[AssessmentFeature]:
        config = get_config()
        all_features = config.services.classification.features

        if feature_codes is None:
            feature_codes = [
                code for code, cfg in all_features.items()
                if code in self.features and cfg.enabled
            ]

        result = []
        for code in feature_codes:
            cfg = all_features.get(code)
            if cfg is None or not cfg.enabled:
                continue
            feature_cls = self.features.get(code)
            if feature_cls is None:
                continue
            result.append(feature_cls())
        return result