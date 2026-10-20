from image_assessment_service.core.aggregation.models import BBox, Image, Segment


class TestAggregationModel:
    def test_bbox_to_dict(self):
        bbox = BBox(123, "cat", coords=[1.0, 2.5, 3.0, 4.5])

        dct = bbox.to_dict()

        assert dct == {
            "id": 123,
            "label": "cat",
            "type": "bbox",
            "coords": [1.0, 2.5, 3.0, 4.5],
        }

    def test_image_to_dict(self):
        image = Image(123, "cat")

        dct = image.to_dict()

        assert dct == {
            "id": 123,
            "label": "cat",
            "type": "image",
        }

    def test_segment_to_dict(self):
        segment = Segment(123, "cat", points=[1.0, 2.5, 3.0, 4.5, 50, 60])

        dct = segment.to_dict()

        assert dct == {
            "id": 123,
            "label": "cat",
            "type": "segment",
            "points": [1.0, 2.5, 3.0, 4.5, 50, 60],
        }
