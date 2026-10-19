from enum import Enum
from typing import Any, Dict, List

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError, field_validator

image_name_forbidden_symbols = {"/", "\\", ":", "*", "?", '"', "<", ">", "|"}


def validate_image_name(name: str):
    if not name:
        raise HTTPException(400, "Имя изображения не может быть пустым")

    if len(name) > 255:
        raise HTTPException(400, "Слишком длинное имя изображения (макс. 255 символов)")

    if set(name).intersection(image_name_forbidden_symbols):
        raise HTTPException(400, f"Некорректное имя изображения: {name}")


class AnnotationType(str, Enum):
    BBOX = "bbox"
    SEGMENT = "segment"
    IMAGE = "image"


class AnnotationData(BaseModel):
    label: str
    type: AnnotationType
    attributes: Dict[str, Any] | None = None

    class Config:
        extra = "forbid"


class BBoxData(AnnotationData):
    coords: List[float]

    @field_validator("coords")
    def check_coords_length(cls, v):
        if len(v) != 4:
            raise ValueError("Должно быть 4 координаты")
        return v


class SegmentData(AnnotationData):
    points: List[float]

    @field_validator("points")
    def check_points_even(cls, v):
        if len(v) % 2 != 0:
            raise ValueError("Должно быть четное количество точек")
        return v


class ImageData(AnnotationData):
    pass


def validate_annotation_data(data: List[Dict[str, Any]]) -> None:
    for item in data:
        if "type" not in item:
            raise HTTPException(400, "Тип аннотации не указан")
        try:
            ann_type = AnnotationType(item["type"])
        except ValueError:
            raise HTTPException(400, "Неизвестный тип аннотации")

        try:
            match ann_type:
                case AnnotationType.BBOX:
                    BBoxData(**item)
                case AnnotationType.SEGMENT:
                    SegmentData(**item)
                case AnnotationType.IMAGE:
                    ImageData(**item)
        except ValidationError as e:
            raise HTTPException(400, f"Некорректные данные аннотации: {e}")
