import random

from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_, func, case

from typing import Dict, List

from image_assessment_service.autorization.models.core import ImageRatings, Images
from image_assessment_service.autorization.controllers.utils import get_current_user
from image_assessment_service.config import get_config

from tqdm import tqdm

_RATING_MAP = {
    '1': 'grade_1',
    '2': 'grade_2',
    '3': 'grade_3',
    '4': 'grade_4',
    '5': 'grade_5',
    '0': 'inappropriate'
}


def init_images(db: Session, init_images_dict: Dict[str, List], code: str):
    for i in tqdm(range(len(init_images_dict["fid"])), desc=f"add images to db for code {code}"):
        db.add(_build_image_row(init_images_dict, i))

    db.commit()


def get_images_by_dict(images_dict: dict, db: Session, code: str):
    rows, indexes_to_remove = _find_existing_images(images_dict, db, code)
    _remove_existing_indexes(images_dict, indexes_to_remove)

    return rows, images_dict


def mark_image(db: Session, type: str, fid: str, token: str, code: str):
    _ensure_valid_rating(type)

    _increment_grade(db, fid, type)
    new_rating = _create_rating(db, token, fid, type, code)

    return _maybe_finalize(db, fid, code, new_rating)


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


def unique_fid_per_user(token: str, db: Session, all_fids: List[str], code: str):
    assessed_fids = _get_user_rated_fids(token, db, code)

    return _pick_unseen_fid(all_fids, assessed_fids), len(assessed_fids)


def get_assess_statistics(token: str, db: Session):
    results = _query_rating_stats(db)
    user = get_current_user(token, db=db)

    return _build_statistics_response(results, user.nickname)


def _build_image_row(init_images_dict: Dict[str, List], i: int) -> Images:
    image = Images()
    image.fid = init_images_dict["fid"][i]
    image.code = init_images_dict["code"][i]
    image.folder = init_images_dict["folder"][i]
    image.name = init_images_dict["name"][i]
    return image


def _find_existing_images(images_dict: dict, db: Session, code: str):
    rows, indexes_to_remove = [], []
    # List for each key has the same length
    for i in tqdm(range(len(images_dict["code"])), desc=f"query the images from db for code {code}"):
        image_code, folder, name = images_dict["code"][i], images_dict["folder"][i], images_dict["name"][i]
        # Query with all three conditions
        row = db.execute(
            select(Images).where(
                (Images.code == image_code) &
                (Images.folder == folder) &
                (Images.name == name)
            )
        ).scalar_one_or_none()  # Gets a single result or None

        if row is not None:
            rows.append(row)
            indexes_to_remove.append(i)

    return rows, indexes_to_remove


def _remove_existing_indexes(images_dict: dict, indexes_to_remove: List[int]) -> None:
    for i in sorted(indexes_to_remove, reverse=True):
        for key in images_dict:
            del images_dict[key][i]


def _ensure_valid_rating(type: str) -> None:
    if type not in _RATING_MAP:
        raise ValueError("Invalid rating type")


def _increment_grade(db: Session, fid: str, type: str) -> None:
    column_to_update = _RATING_MAP[type]

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


def _create_rating(db: Session, token: str, fid: str, type: str, code: str) -> ImageRatings:
    user = get_current_user(token, db=db)
    new_rating = ImageRatings(
        user_nickname=user.nickname,
        image_fid=fid,
        rating=int(type),
        image_code=code
    )
    db.add(new_rating)

    return new_rating


def _maybe_finalize(db: Session, fid: str, code: str, new_rating: ImageRatings):
    image_row = db.scalar(select(Images).where(Images.fid == fid))
    feature = get_config().feature_config(code)
    vote_number_per_code = feature.vote_number if feature else 0

    if not _is_finalized(image_row, vote_number_per_code):
        db.commit()
        db.refresh(new_rating)
        return False

    score = _compute_score(image_row)
    _mark_annotated(db, fid)
    db.commit()
    db.refresh(new_rating)

    return score


def _is_finalized(image_row, vote_number_per_code: int) -> bool:
    return image_row and (image_row.grade_1 + image_row.grade_2 + image_row.grade_3
                          + image_row.grade_4 + image_row.grade_5 + image_row.inappropriate) >= vote_number_per_code


def _compute_score(image_row) -> int:
    return round(
        (1 * image_row.grade_1 + 2 * image_row.grade_2 + 3 * image_row.grade_3
         + 4 * image_row.grade_4 + 5 * image_row.grade_5) / 3
    )


def _mark_annotated(db: Session, fid: str) -> None:
    db.execute(
        update(Images)
        .where(Images.fid == fid)
        .values(annotated=True)
    )


def _get_user_rated_fids(token: str, db: Session, code: str) -> List[str]:
    user = get_current_user(token, db=db)

    rated_fids = db.query(ImageRatings.image_fid) \
        .filter(ImageRatings.user_nickname == user.nickname) \
        .filter(ImageRatings.image_code == code) \
        .all()

    return [str(fid[0]) for fid in rated_fids]


def _pick_unseen_fid(all_fids: List[str], assessed_fids: List[str]):
    set_all_fids = set(all_fids)
    set_assessed_fids = set(assessed_fids)

    not_seen_fids = list(set_all_fids - set_assessed_fids)

    if len(not_seen_fids) > 1:
        return random.choice(not_seen_fids)
    if len(not_seen_fids) == 1:
        return not_seen_fids[0]

    return None


def _query_rating_stats(db: Session):
    # Database query using SQLAlchemy
    stmt = (
        select(
            ImageRatings.user_nickname,
            func.count().label("rating_count")
        )
        .group_by(ImageRatings.user_nickname)
        .order_by(func.count().desc())
    )

    return db.execute(stmt).all()


def _build_statistics_response(results, current_user_nickname: str):
    return {
        "stats": [{
            "nickname": nickname,
            "count": count
        } for nickname, count in results],
        "current_user_nickname": current_user_nickname
    }