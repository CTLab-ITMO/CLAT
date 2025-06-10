import random
from datetime import datetime, timedelta

import pytest
from image_assessment_service.autorization.controllers.users import register
from image_assessment_service.autorization.models.schemas import UserCreate


@pytest.fixture
def create_test_user(db_session):
    async def inner():
        email = f"user{random.randint(1000, 9999)}@email.com"
        password = "1234"

        user_create = UserCreate(email=email, password=password)

        user = register(db_session(), user_create)

        return user["id"]

    return inner
