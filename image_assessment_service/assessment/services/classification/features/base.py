import uuid
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session
from tqdm import tqdm

from image_assessment_service.assessment.services.base import AssessmentService
from image_assessment_service.autorization.controllers.image_ratings import (
    get_images_by_dict,
    init_images,
    mark_image,
    unique_fid_per_user,
)
from image_assessment_service.storages import Storages


class AssessmentFeature(AssessmentService):
    """Фича сервиса классификации: выборка случайного изображения, голосование, метрики.

    Пути фича резолвит сама через свой конфиг: полный путь берётся из ``services.classification.features[code].path``.
    """

    def __init__(self):
        super().__init__()
        self._samples: Dict[str, Tuple[str, str, str]] = {}
        self._all = 0
        self._answers = 0
        self._inited = False
        self._init_images_dict: Optional[dict] = None

    @property
    def assess_type(self) -> Optional[str]:
        return self._cfg.assess_type

    @property
    def vote_number(self) -> int:
        return self._cfg.vote_number

    def init(self, db: Session) -> None:
        if self._inited:
            return

        if self.assess_type == "continue":
            self._continue_assessment(db)
        elif self.assess_type == "new":
            self._start_new_assessment(db)
        else:
            self._inited = True

    def rand_fid(self, token: str, db: Session) -> Tuple[Optional[str], int]:
        """Вернуть случайный fid изображения, которое юзер ещё не оценивал."""
        self.init(db)
        fid, user_answers = unique_fid_per_user(
            token=token, db=db, all_fids=list(self._samples.keys()), code=self.code
        )
        return fid, user_answers

    def get(self, fid: str) -> Tuple[str, str, str]:
        return self._samples[fid]

    def mark(self, fid: str, type: str, token: str, db: Session) -> None:
        """Поставить оценку изображению и обновить статистику."""
        if fid is None or len(fid) == 0:
            return
        f = self._samples.get(fid, None)
        if f is None:
            return

        score = mark_image(db=db, type=type, fid=fid, token=token, code=self.code)
        self._answers += 1

        if score:
            self._samples.pop(fid)

    def size(self) -> int:
        return len(self._samples)

    def all(self) -> int:
        return self._all

    def answers(self) -> int:
        return self._answers

    # ---- internals ----

    def _continue_assessment(self, db: Session) -> None:
        self._create_init_images_dict()
        rows, init_images_dict = get_images_by_dict(
            images_dict=self._init_images_dict, db=db, code=self.code
        )
        self._collect_existing_ratings(rows)

        if len(init_images_dict["code"]) > 0:
            init_images(db=db, init_images_dict=init_images_dict, code=self.code)
            self._add_samples(init_images_dict)

        self._inited = True
        self._all = len(self._samples)

    def _collect_existing_ratings(self, rows) -> None:
        for row in rows:
            self._answers += row.grade_1 + row.grade_2 + row.grade_3 + row.grade_4 + row.grade_5 + row.inappropriate

            if not row.annotated:
                self._samples[str(row.fid)] = (row.code, row.folder, row.name)

    def _start_new_assessment(self, db: Session) -> None:
        if not self._init_images_dict:
            self._create_init_images_dict()

        init_images(db=db, init_images_dict=self._init_images_dict, code=self.code)
        self._add_samples(self._init_images_dict)
        self._all = len(self._samples)
        self._inited = True

    def _create_init_images_dict(self) -> None:
        self._init_images_dict = {
            "fid": [],
            "code": [],
            "folder": [],
            "name": [],
        }

        for f in tqdm(
            Storages().get(self.code).walkdir(exts=[".jpg", ".jpeg", ".png"]),
            desc=f"initialize image dict for code {self.code}",
        ):
            u = str(uuid.uuid4())
            self._init_images_dict["fid"].append(u)
            self._init_images_dict["code"].append(f[0])
            self._init_images_dict["folder"].append(f[1])
            self._init_images_dict["name"].append(f[2])

    def _add_samples(self, images_dict: dict) -> None:
        for i in range(len(images_dict["code"])):
            fid, code, folder, name = (
                images_dict["fid"][i],
                images_dict["code"][i],
                images_dict["folder"][i],
                images_dict["name"][i],
            )
            self._samples[str(fid)] = (code, folder, name)