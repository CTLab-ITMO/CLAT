import asyncio
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from image_assessment_service.cli import parse_args
from image_assessment_service.config import get_config, load_config
from locust import HttpUser, between, events, task
from sqlalchemy import text

load_dotenv()
config_path = Path("local.config.yaml")
load_config(config_path)
config = get_config()

from image_assessment_service.core.services.annotation_service import annotationService

ID_START_MAGIC_CONSTANT = 12321312


class ImageAssessmentUser(HttpUser):
    host = f"http://localhost:{config.application.port}"
    # wait_time = between(0.05, 0.1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = ID_START_MAGIC_CONSTANT + random.randint(0, config.test.user_count - 1)
        self.token = f"loadtest_token_{self.user_id}"
        self.current_fid = None
        self.annotation_id = asyncio.run(annotationService.get_annotations(self.user_id))[0].annotation_id


    # @task(3)
    def get_image(self):
        self.client.verify = False
        with self.client.get(
                "/assess/tech/get",
                params={"token": self.token, "code": "tech"},
                name="(1) Get Image"
        ) as response:
            if response.ok:
                data = response.json()
                self.current_fid = data.get("fid")

    # @task(1)
    def rate_image(self):
        self.client.verify = False
        if not self.current_fid:
            return

        rating = str(random.randint(1, 5))  # Convert to string since endpoint expects str
        with self.client.post(
                "/assess/tech/mark?",
                params={
                    "fid": self.current_fid,
                    "type": rating,  # Note: endpoint expects 'type' as string
                    "token": self.token,
                    "code": "tech"
                },
                name="(3) Rate Image"
        ) as response:
            if response.ok:
                self.current_fid = None
    
    # @task(1)
    def load_annotation(self):
        self.client.verify = False

        with self.client.get(
                f"/api/annotations/{self.annotation_id}/images/pic3",
                headers={
                    'Authorization': self.token
                },
                name="(1) Load Annotation"
        ) as response:
            if response.ok:
                pass
    
    @task(1)
    def save_annotation(self):
        self.client.verify = False
        with self.client.post(
                f"/api/annotations/{self.annotation_id}/images/pic3",
                headers={
                    'Authorization': self.token
                },
                json=[{'id': 1, 'label': 'dog', 'type': 'bbox', 'coords': [1400.5, 667, 1752.5, 811]}]
        ) as response:
            if response.ok:
                pass


# @events.test_start.add_listener
# def on_test_start(environment, **kwargs):
#     if not os.getenv("SKIP_DATA_CHECK"):
#         from sqlalchemy import create_engine
#         engine = create_engine(config.postgres.get_database_url())
#         with engine.connect() as conn:
#             # Wrap SQL in text()
#             user_count = db.query(User).filter(User.email.like(f"{config.test.test_user_prefix}%")).scalar()
#             if user_count < config.test.user_count:
#                 raise Exception(f"Need {config.test.user_count} test users")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Optional: Clean up test data"""
    if os.getenv("CLEAN_AFTER_TEST"):
        from test_data import init_test_data
        init_test_data()  # Re-initializes fresh data