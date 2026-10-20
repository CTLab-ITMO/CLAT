import os
import pathlib
from typing import Dict, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator

from fastapi.templating import Jinja2Templates
from pathlib import Path


class LoadTestConfig(BaseModel):
    user_count: int = Field(1, description="User port")
    host_url: str = Field("http://localhost:8000", description="Host url")
    spawn_rate: int = Field(1, description="Spawn rate")
    test_duration: str = Field("5m", description="Test duration")
    test_user_prefix: str = Field("loadtest_user", description="User prefix")
    test_password: str = Field("testpass123", description="test_pass_123")


class ApplicationConfig(BaseModel):
    name: str = Field("image-assessment-service", description="Service name")
    host: str = Field("0.0.0.0", description="Host to bind to")
    port: int = Field(5000, description="Service port")

    @field_validator('port')
    def port_must_be_valid(cls, v):
        if not 0 < v < 65536:
            raise ValueError('Port must be between 1 and 65535')
        return v


class PostgresConfig(BaseModel):
    host: str = Field("localhost", description="Postgres host")
    port: int = Field(5432, description="Postgres port")
    dbname: str = Field("mydatabase", description="Database name")
    table_name: str = Field("image_ratings", description="Database table name")
    user: str = Field("myuser", description="Database user")
    password: Optional[str] = Field(None, description="Database password")

    def get_database_url(self) -> str:
        pconf = get_config().postgres
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


class ServiceConfig(BaseModel):
    enabled: bool = Field(True, description="Service enabled flag")
    path: str = Field(..., description="Full path to the service data")


class ServiceFeatureConfig(ServiceConfig):
    code: Optional[str] = Field(None, description="Feature code, set automatically from config key")
    assess_type: Optional[str] = Field(None, description="Assessment type [None | continue | new]")
    vote_number: int = Field(0, description="The number of votes are needed to finish assessing for image")
    example_dir: Optional[str] = Field(None, description="Full path to directory with classification examples")


class ClassificationServiceConfig(BaseModel):
    enabled: bool = Field(True, description="Service enabled flag")
    features: Dict[str, ServiceFeatureConfig] = Field(default_factory=dict)

    @field_validator('features', mode='before')
    def transform_feature_keys(cls, v):
        """Преобразует {'tech': {...}} в {'tech': {'code': 'tech', ...}}"""
        if not isinstance(v, dict):
            return v
        return {
            key: {**value, "code": key}
            for key, value in v.items()
        }


class ServicesConfig(BaseModel):
    detection: ServiceConfig
    segmentation: ServiceConfig
    classification: ClassificationServiceConfig


class Config(BaseModel):
    test: LoadTestConfig = Field(default_factory=LoadTestConfig)
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    services: ServicesConfig

    def feature_config(self, code: str) -> Optional[Union[ServiceConfig, ServiceFeatureConfig]]:
        """Возвращает конфиг сервиса/фичи по коду."""
        if code == "detection":
            return self.services.detection
        if code == "segmentation":
            return self.services.segmentation
        return self.services.classification.features.get(code)

    @classmethod
    def load(cls, dict_config: dict) -> 'Config':
        return cls.model_validate(dict_config)


_config_instance = None


def load_config(config_path: pathlib.Path) -> None:
    global _config_instance
    if _config_instance is not None:
        raise RuntimeError("Config already loaded")

    with open(config_path, encoding="utf-8") as f:
        config_dict = yaml.safe_load(f) or {}

    postgres_env = {
        "host": "POSTGRES_HOST",
        "port": "POSTGRES_PORT",
        "dbname": "POSTGRES_DATABASE",
        "user": "POSTGRES_USER",
        "password": "POSTGRES_PASSWORD",
    }
    postgres_conf = config_dict.setdefault("postgres", {})
    for key, env_name in postgres_env.items():
        value = os.getenv(env_name)
        if value is not None:
            postgres_conf[key] = value

    if not postgres_conf.get("password"):
        raise RuntimeError("Postgres password must be provided")

    _config_instance = Config.model_validate(config_dict)


def get_config() -> Config:
    if _config_instance is None:
        raise RuntimeError("Config not loaded")
    return _config_instance


_templates_instance = None


def get_templates():
    global _templates_instance
    if _templates_instance is None:
        _templates_instance = Jinja2Templates(directory=Path(__file__).resolve().parent / 'templates')
    return _templates_instance