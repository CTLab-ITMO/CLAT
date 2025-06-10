import random

from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_, func, case

from typing import Dict

from typing import List

from image_assessment_service.autorization.models.core import ImageRatings, Images
from image_assessment_service.autorization.controllers.utils import get_current_user
from image_assessment_service.config import get_config

config = get_config()

def init_images(db: Session, init_images_dict: Dict[str, List]):
    for i in range(len(init_images_dict["fid"])):
        image = Images()
        image.fid = init_images_dict["fid"][i]
        image.code = init_images_dict["code"][i]
        image.folder = init_images_dict["folder"][i]
        image.name = init_images_dict["name"][i]
        db.add(image)

    db.commit()
    return

def get_images_by_dict(images_dict: dict, db: Session):
    # Query the Images table for rows with the given code
    rows, indexes_to_remove = [], []
    # List for each key has the same length
    for i in range(len(images_dict["code"])):
        code, folder, name = images_dict["code"][i], images_dict["folder"][i], images_dict["name"][i]
        # Query with all three conditions
        row = db.execute(
            select(Images).where(
                (Images.code == code) &
                (Images.folder == folder) &
                (Images.name == name)
            )
        ).scalar_one_or_none()  # Gets a single result or None

        if row is not None:
            rows.append(row)
            indexes_to_remove.append(i)

    for i in sorted(indexes_to_remove, reverse=True):
        for key in images_dict:
            del images_dict[key][i]

    return rows, images_dict

def mark_image(db: Session, type: str, fid: str, token: str, code: str):
    rating_map = {
        '1': 'grade_1',
        '2': 'grade_2',
        '3': 'grade_3',
        '4': 'grade_4',
        '5': 'grade_5',
        '0': 'inappropriate'  # Keep as '0' for consistency
    }

    if type not in rating_map:
        raise ValueError("Invalid rating type")

    column_to_update = rating_map[type]

    update_stmt = (
        update(Images)
        .where(Images.fid == fid)
        .values({
            column_to_update: case(
                (Images.__table__.c[column_to_update] == None, 1),
                else_=Images.__table__.c[column_to_update] + 1
            )
        })
    )
    db.execute(update_stmt)

    user = get_current_user(token, db=db)
    new_rating = ImageRatings(
        user_nickname=user.nickname,
        image_fid=fid,
        rating=int(type),
        image_code=code
    )
    db.add(new_rating)

    image_row = db.scalar(select(Images).where(Images.fid == fid))
    vote_number_per_code = config.storages.get(code).vote_number
    if image_row and (image_row.grade_1 + image_row.grade_2 + image_row.grade_3
                      + image_row.grade_4 + image_row.grade_5 + image_row.inappropriate) >= vote_number_per_code:
        score = round(
            (1 * image_row.grade_1 + 2 * image_row.grade_2 + 3 * image_row.grade_3 + 4 * image_row.grade_4 + 5 * image_row.grade_5) / 3
        )

        # Set the annotated flag to True
        db.execute(
            update(Images)
            .where(Images.fid == fid)
            .values(annotated=True)
        )

        db.commit()
        db.refresh(new_rating)

        return score

    else:
        db.commit()
        db.refresh(new_rating)

        return False

def has_image_ratings(image_code: str, db: Session):

    # Query to check if any ratings exist for the given image code
    stmt = (
        select(ImageRatings)
        .join(
            Images,
            and_(
                ImageRatings.image_fid == Images.fid,
                ImageRatings.image_code == Images.code
            )
        )
        .where(Images.code == image_code)
    )
    # Execute the query and check if any results exist
    result = db.scalar(stmt)
    return result is not None

def unique_fid_per_user(token: str, db: Session, all_fids: List[str], code:str):
    user = get_current_user(token, db=db)

    # Query to get all image FIDs the user has rated
    rated_fids = db.query(ImageRatings.image_fid) \
        .filter(ImageRatings.user_nickname == user.nickname) \
        .filter(ImageRatings.image_code == code) \
        .all()

    assessed_fids = [str(fid[0]) for fid in rated_fids]
    user_answers = len(assessed_fids)

    set_all_fids = set(all_fids)
    set_assessed_fids = set(assessed_fids)

    not_seen_fids = list(set_all_fids - set_assessed_fids)

    if len(not_seen_fids) > 1:
        unique_unseen_fid = random.choice(not_seen_fids)
    elif len(not_seen_fids) == 1:
        unique_unseen_fid = not_seen_fids[0]
    else:
        unique_unseen_fid = None

    return unique_unseen_fid, user_answers

def get_assess_statistics(token: str, db: Session):
    # Database query using SQLAlchemy
    stmt = (
        select(
            ImageRatings.user_nickname,
            func.count().label("rating_count")
        )
        .group_by(ImageRatings.user_nickname)
        .order_by(func.count().desc())
    )

    results = db.execute(stmt).all()
    user = get_current_user(token, db=db)

    response = {
        "stats": [{
            "nickname": nickname,
            "count": count
        } for nickname, count in results],
        "current_user_nickname": user.nickname
    }

    return response
