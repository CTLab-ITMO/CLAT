import pytest
from image_assessment_service.dependencies import get_container


@pytest.fixture(autouse=True)
def setup_before_mocks(mock_container):
    # Необходимо для DI сервисов
    print("\n=== Инициализация перед моками ===")
    yield
    print("\n=== Очистка после теста ===")


expected_scores_data = [
    {
        "id": "2",
        "macro_accuracy": 1.0,
        "micro_accuracy": 0.9,
    },
    {
        "id": "1",
        "macro_accuracy": 0.5,
        "micro_accuracy": 0.45,
    },
]


def check_scores_file(file_path, expected_data):
    keys = ["id", "nickname", "email", "macro_accuracy", "micro_accuracy"]
    scores = []

    with open(file_path, "r") as f:

        assert f.readline()[:-1] == ",".join(keys)

        for idx, line in enumerate(f):
            row = {k: v for k, v in zip(keys, line.split(","))}

            assert row["id"] == expected_data[idx]["id"]

            macro_acc = float(row["macro_accuracy"])
            micro_acc = float(row["micro_accuracy"])

            assert macro_acc == pytest.approx(
                expected_data[idx]["macro_accuracy"], rel=1e-2
            )
            assert micro_acc == pytest.approx(
                expected_data[idx]["micro_accuracy"], rel=1e-2
            )

            scores.append(row)

    assert len(scores) == len(expected_data)


@pytest.mark.asyncio
async def test_aggregate_annotations_success(
    create_test_task_1,
    create_test_annotation,
    annotation_data_1,
    annotation_data_2,
    create_test_user,
):

    task_id = await create_test_task_1

    user_id_1 = await create_test_user()
    user_id_2 = await create_test_user()

    annotation_id_1 = await create_test_annotation(
        task_id=task_id,
        user_id=user_id_1,
        image_name_to_data={"image1.jpg": annotation_data_1},
    )
    annotation_id_2 = await create_test_annotation(
        task_id=task_id,
        user_id=user_id_2,
        image_name_to_data={"image1.jpg": annotation_data_2},
    )

    annotations = [
        await get_container().annotation_service.get_annotation(annotation_id_1),
        await get_container().annotation_service.get_annotation(annotation_id_2),
    ]

    annotation_id_res = await get_container().aggregation_service.aggregate_annotations(
        annotations, 0.5, 2
    )

    ann_data = await get_container().annotation_service.get(
        annotation_id_res, "image1.jpg"
    )
    assert len(ann_data) == 1
    assert ann_data[0] == {
        "id": 0,
        "label": "cat",
        "type": "bbox",
        "coords": [11.0, 20.0, 31.0, 40.0],
    }

    scores_file_path = await get_container().annotation_service.get_scores_path(
        annotation_id_res
    )

    check_scores_file(scores_file_path, expected_scores_data)
