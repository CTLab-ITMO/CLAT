from image_assessment_service.core.aggregation.models import BBox


class TestAggregationModel:
    def test_to_dict(self):
        bbox = BBox(123, "cat", coords=[1.0, 2.5, 3.0, 4.5])

        dct = bbox.to_dict()

        assert dct == {
            "id": 123,
            "label": "cat",
            "type": "bbox",
            "coords": [1.0, 2.5, 3.0, 4.5],
        }
