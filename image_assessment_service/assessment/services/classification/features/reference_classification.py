from pathlib import Path
from typing import Optional

from image_assessment_service.assessment.services.classification.features.base import AssessmentFeature


class ReferenceClassificationFeature(AssessmentFeature):
    """РљР»Р°СЃСЃРёС„РёРєР°С†РёСЏ РїРѕ СЂРµС„РµСЂРµРЅСЃСѓ: РѕРїСЂРµРґРµР»РµРЅРёРµ РєР»Р°СЃСЃР° РёР·РѕР±СЂР°Р¶РµРЅРёСЏ, СЃРІРµСЂСЏСЏСЃСЊ СЃ РїСЂРёРјРµСЂР°РјРё."""

    code = "classify"

    @property
    def example_dir(self) -> Optional[Path]:
        """РџРѕР»РЅС‹Р№ РїСѓС‚СЊ Рє РїР°РїРєРµ РїСЂРёРјРµСЂРѕРІ, Р±РµСЂС‘С‚СЃСЏ РёР· РєРѕРЅС„РёРіР° С„РёС‡Рё."""
        if self._cfg.example_dir:
            return Path(self._cfg.example_dir)
        return None

    def class_example(self, class_name: str) -> Optional[Path]:
        """РџСѓС‚СЊ Рє РїСЂРёРјРµСЂСѓ РєР»Р°СЃСЃР° (img1.jpg) РёР»Рё None, РµСЃР»Рё РїСЂРёРјРµСЂС‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹."""
        if self.example_dir is None:
            return None
        return self.example_dir / class_name / "img1.jpg"

