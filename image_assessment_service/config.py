import os
import pathlib
from typing import Dict, Any

from omegaconf import OmegaConf
from pydantic import BaseModel, Field
from pydantic import field_validator

from fastapi.templating import Jinja2Templates
from pathlib import Path

_base_config = {
        'application': {
        'name': 'image-assessment-service',
        'host': '0.0.0.0',
        'port': 5000
    },
    'postgres': {
        'host': '0.0.0.0',
        'port': 5432,
        'dbname': 'mydatabase',
        'table_name': 'image_ratings',
        'user': 'myuser'
    },
    'storages': {
        'tech': {
            'path': 'data/images/test_images',
            'out_path': 'data/assessed_images'
        },
        'aesth': {
            'path': 'data/images/test_images',
            'out_path': 'data/assessed_images'
        }
    },
    'tasks': {
        'base_path': 'data/tasks_data'
    }
}

class LoadTestConfig(BaseModel):
    user_count: int = Field(..., description="User port")
    host_url: str = Field(..., description="Host url")
    spawn_rate: int = Field(..., description="Spawn rate")
    test_duration: str = Field(..., description="Test duration")
    test_user_prefix: str = Field(..., description="User prefix")
    test_password: str = Field(..., description="test_pass_123")

class ApplicationConfig(BaseModel):
    name: str = Field(..., description="Service name")
    host: str = Field(..., description="Host to bind to")
    port: int = Field(..., description="Service port")
    
    @field_validator('port')
    def port_must_be_valid(cls, v):
        if not 0 < v < 65536:
            raise ValueError('Port must be between 1 and 65535')
        return v

class PostgresConfig(BaseModel):
    host: str = Field(..., description="Postgres host")
    port: int = Field(..., description="Postgres port")
    dbname: str = Field(..., description="Database name")
    table_name: str = Field(..., description="Database table name")
    user: str = Field(..., description="Database user")
    password: str = Field(..., description="Database password")

    def get_database_url(self) -> str:
        pconf = get_config().postgres
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

class LocalStorageConfig(BaseModel):
    code: str = Field(..., description="List of storage codes")
    continue_assess: bool = Field(False, description="Continue assessment flag")
    path: str = Field(..., description="Base path for service")
    out_path: str = Field(..., description="Output path for processed files")
    vote_number: int = Field(..., description="The number of votes are needed to finish assessing for image")

class AnnotationTasksConfig(BaseModel):
    base_path: str = Field(..., description="Base path for tasks")
    
class Config(BaseModel):
    test: LoadTestConfig = Field(default=None, description="Test configuration")
    application: ApplicationConfig
    postgres: PostgresConfig
    storages: Dict[str, LocalStorageConfig]
    tasks: AnnotationTasksConfig

    @field_validator('storages', mode='before')
    def transform_storage_keys(cls, v):
        """Преобразует {'tech': {...}} в {'tech': {'code': 'tech', ...}}"""
        return {
            key: {**value, "code": key}
            for key, value in v.items()
        }

    @classmethod
    def load(cls, dict_config: dict) -> 'Config':
        return cls.model_validate(dict_config)


_config_instance = None


def load_config(config_path: pathlib.Path) -> None:
    global _config_instance
    if _config_instance is not None:
        raise RuntimeError("Config already loaded")
    
    stage_config = OmegaConf.load(config_path)
    config = OmegaConf.merge(_base_config, stage_config)

    postgres_password = os.getenv("POSTGRES_PASSWORD")
    if not postgres_password and not config.postgres.get("password"):
        raise RuntimeError("Postgres password must be provided")
    else:
        config.postgres['password'] = postgres_password

    config_dict = OmegaConf.to_container(config, resolve=True)
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