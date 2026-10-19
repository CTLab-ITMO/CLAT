from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from image_assessment_service.apis.feature_api import create_assessment_router
from image_assessment_service.assessment.services.registry import get_feature


def _classify_file_info(f) -> dict:
    p = Path(f[1])
    main_dir = p.parts[0]

    if "__" in main_dir:
        model_class1, model_class2 = main_dir.split("__", 1)
    else:
        model_class1, model_class2 = main_dir, ""

    return {
        'storage': f[0],
        'path': f[1],
        'name': f[2],
        'model_class1': model_class1,
        'model_class2': model_class2,
    }


classify_api = create_assessment_router("classify", file_info=_classify_file_info)


@classify_api.get('/class_example')
def get_class_example(class_example: str):
    feature = get_feature("classify")
    if feature is None or not feature.enabled:
        raise HTTPException(503, "Classify feature is not enabled")

    example_path = feature.class_example(class_example)
    if example_path is None:
        raise HTTPException(503, "Classify feature or example_dir is not configured")

    return FileResponse(example_path)