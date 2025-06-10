from image_assessment_service.autorization.models.core import (
    Annotation,
    ImageRatings,
    Images,
    Token,
    User,
)
from image_assessment_service.cli import parse_args
from image_assessment_service.config import get_config, load_config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import asyncio

args = parse_args()
load_config(args.config_path)
config = get_config()

from image_assessment_service.core.services.annotation_service import annotationService
from image_assessment_service.services import SamplesService

ID_START_MAGIC_CONSTANT = 12321312


def init_test_data():
    engine = create_engine(config.postgres.get_database_url())
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Clear existing test data
        db.query(Annotation).filter(Annotation.user_id == User.id, User.email.like(f"{config.test.test_user_prefix}%")).delete()
        db.query(ImageRatings).filter(ImageRatings.user_nickname.like("tester_%")).delete()
        db.query(Images).filter(Images.folder == "test_data").delete()
        db.query(Token).filter(Token.access_token.like("loadtest_%")).delete()
        db.query(User).filter(User.email.like(f"{config.test.test_user_prefix}%")).delete()

        # Create test users and get their IDs
        users = []
        for i in range(config.test.user_count):
            user = User(
                id=(ID_START_MAGIC_CONSTANT + i),
                email=f"{config.test.test_user_prefix}_{i}@example.com",
                hashed_password=config.test.test_password,
                nickname=f"tester_{i}"
            )
            db.add(user)
            db.flush()  # Force DB to generate ID
            users.append(user)

        db.commit()  # Final commit for users

        for u in users:
            asyncio.run(annotationService.create_annotation(4, u.id))

        # Now create tokens with valid user IDs
        tokens = [
            Token(
                access_token=f"loadtest_token_{users[i].id}",
                user_id=users[i].id  # This will now have the proper ID
            )
            for i in range(len(users))
        ]
        db.bulk_save_objects(tokens)
        db.commit()

        images = []
        # Create test images
        service = SamplesService(code="tech", db=db)
        print(f"Created {len(users)} users, {len(tokens)} tokens, {service.size()} images, {len(users)} annotations")

        rand_fid, _ = service.rand_fid(code="test", token=tokens[0].access_token, db=db)
        service.mark(fid=rand_fid, type="4", code="tech", token=tokens[0].access_token, db=db)

    finally:
        db.close()

if __name__ == "__main__":
    init_test_data()