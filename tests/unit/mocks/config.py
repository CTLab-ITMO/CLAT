import pytest
from image_assessment_service.config import Config


@pytest.fixture
def mock_config(monkeypatch, tmp_path):
    base_test_config = {
        "application": {
            "name": "",
            "host": "",
            "port": 1,
        },
        "postgres": {
            "host": "",
            "port": 1,
            "dbname": "",
            "table_name": "",
            "user": "",
            "password": "",
        },
        "storages": {
            "tech": {
                "path": "",
                "out_path": "",
            },
            "aesth": {
                "path": "",
                "out_path": "",
            },
        },
        "tasks": {"base_path": str(tmp_path / "data/tasks_data")},
    }

    _config_instance = Config.model_validate(base_test_config)

    monkeypatch.setattr(
        "image_assessment_service.config._config_instance", _config_instance
    )

    print("Mock config created")
