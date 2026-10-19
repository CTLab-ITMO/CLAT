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
        "services": {
            "detection": {
                "enabled": True,
                "path": str(tmp_path / "data/tasks_data"),
            },
            "segmentation": {
                "enabled": True,
                "path": str(tmp_path / "data/tasks_data"),
            },
            "classification": {
                "enabled": True,
                "features": {
                    "tech": {
                        "enabled": True,
                        "assess_type": "continue",
                        "vote_number": 0,
                        "path": str(tmp_path / "data/images"),
                    },
                    "aesth": {
                        "enabled": True,
                        "assess_type": "continue",
                        "vote_number": 0,
                        "path": str(tmp_path / "data/images"),
                    },
                    "filter": {
                        "enabled": True,
                        "assess_type": "continue",
                        "vote_number": 0,
                        "path": str(tmp_path / "data/images"),
                    },
                    "classify": {
                        "enabled": False,
                        "assess_type": "continue",
                        "vote_number": 0,
                        "path": str(tmp_path / "data/images"),
                        "example_dir": str(tmp_path / "data/example_data"),
                    },
                },
            },
        },
    }

    _config_instance = Config.model_validate(base_test_config)

    monkeypatch.setattr(
        "image_assessment_service.config._config_instance", _config_instance
    )

    print("Mock config created")