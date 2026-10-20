import json

import pytest
from fastapi import HTTPException
from image_assessment_service.validation import validate_annotation_data


def test_valid_bbox_json():
    json_data = """
    [
        {
            "label": "test",
            "type": "bbox",
            "coords": [10, 10, 20, 20]
        }
    ]
    """
    data = json.loads(json_data)
    validate_annotation_data(data)


def test_invalid_bbox_missing_coords_json():
    json_data = """
    [
        {
            "label": "test",
            "type": "bbox"
        }
    ]
    """
    data = json.loads(json_data)
    with pytest.raises(HTTPException):
        validate_annotation_data(data)


def test_valid_segment_json():
    json_data = """
    [
        {
            "label": "test",
            "type": "segment",
            "points": [10, 10, 20, 20, 30, 30]
        }
    ]
    """
    data = json.loads(json_data)
    validate_annotation_data(data)


def test_invalid_segment_odd_points_json():
    json_data = """
    [
        {
            "label": "test",
            "type": "segment",
            "points": [10, 10, 20]
        }
    ]
    """
    data = json.loads(json_data)
    with pytest.raises(HTTPException):
        validate_annotation_data(data)


def test_valid_image_json():
    json_data = """
    [
        {
            "label": "test",
            "type": "image",
            "attributes": {"source": "camera"}
        }
    ]
    """
    data = json.loads(json_data)
    validate_annotation_data(data)


def test_invalid_type_json():
    json_data = """
    [
        {
            "label": "test",
            "type": "polygon",
            "points": [10, 10, 20, 20]
        }
    ]
    """
    data = json.loads(json_data)
    with pytest.raises(HTTPException):
        validate_annotation_data(data)


def test_extra_field_json():
    json_data = """
    [
        {
            "label": "test",
            "type": "bbox",
            "coords": [10, 10, 20, 20],
            "extra": "field"
        }
    ]
    """
    data = json.loads(json_data)
    with pytest.raises(HTTPException):
        validate_annotation_data(data)


def test_multiple_valid_annotations_json():
    json_data = """
    [
        {
            "label": "test",
            "type": "bbox",
            "coords": [10, 10, 20, 20]
        },
        {
            "label": "test",
            "type": "segment",
            "points": [10, 10, 20, 20]
        }
    ]
    """
    data = json.loads(json_data)
    validate_annotation_data(data)


def test_empty_list_json():
    json_data = "[]"
    data = json.loads(json_data)
    validate_annotation_data(data)
