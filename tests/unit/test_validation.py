from fastapi import HTTPException
import pytest
from image_assessment_service.validation import validate_image_name


def test_image_name_validation():
    # Проверка валидных имён
    validate_image_name("image123.jpg")
    validate_image_name("my-image.png")
    validate_image_name("картинка.png.jpg")

    # Проверка невалидных имён
    with pytest.raises(HTTPException):
        validate_image_name("../hack")

    with pytest.raises(HTTPException):
        validate_image_name("image*")
