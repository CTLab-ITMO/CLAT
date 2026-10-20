import os
import uuid

from image_assessment_service.storages import Storages
from image_assessment_service.autorization.controllers.image_ratings import init_images, mark_image, has_image_ratings, \
    get_images_by_dict, unique_fid_per_user
from image_assessment_service.autorization.models.database import get_db
from image_assessment_service.config import get_config

from fastapi import Depends

from pathlib import Path

from sqlalchemy.orm import Session

from tqdm import tqdm


config = get_config()

DB_CONFIG = {
    'dbname': config.postgres.dbname,
    'user': config.postgres.user,
    'password': config.postgres.password,
    'host': config.postgres.host,
    'port': config.postgres.port
}

column_mapping = {
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
}

table_name = config.postgres.table_name

class SamplesService:
    def __init__(self, code, db: Session):
        self.__samples = {}
        self.__all = 0
        self.__answers = 0
        self.__inited = False
        self.__init_images_dict: None | dict = None

        if self.__inited:
            return

        if config.storages.get(code).assess_type == "continue":
            self.create_init_images_dict(code)
            rows, init_images_dict = get_images_by_dict(images_dict=self.__init_images_dict, db=db, code=code)
            for row in rows:
                self.__answers += row.grade_1 + row.grade_2 + row.grade_3 + row.grade_4 + row.grade_5 + row.inappropriate

                if not row.annotated:
                    self.__samples[str(row.fid)] = (row.code, row.folder, row.name)

            if len(init_images_dict["code"]) > 0:
                init_images(db=db, init_images_dict=init_images_dict, code=code)
                self.add_samples(init_images_dict)

            self.__inited = True
            self.__all = len(self.__samples)

            return

        elif config.storages.get(code).assess_type == "new":

            if not self.__init_images_dict:
                self.create_init_images_dict(code)

            init_images(db=db, init_images_dict=self.__init_images_dict, code=code)
            self.add_samples(self.__init_images_dict)
            self.__all = len(self.__samples)
            self.__inited = True

        else:
            self.__inited = True
            return

    def create_init_images_dict(self, code):
        self.__init_images_dict = {
            "fid": [],
            "code": [],
            "folder": [],
            "name": []
        }

        for f in tqdm(Storages().get(code).walkdir(exts=[".jpg", ".jpeg", ".png"]), desc=f"initialize image dict for code {code}"):
            u = str(uuid.uuid4())
            self.__init_images_dict["fid"].append(u)
            self.__init_images_dict["code"].append(f[0])
            self.__init_images_dict["folder"].append(f[1])
            self.__init_images_dict["name"].append(f[2])

    def add_samples(self, images_dict: dict):
        for i in range(len(images_dict["code"])):
            fid, code, folder, name = images_dict["fid"][i], images_dict["code"][i], images_dict["folder"][i], images_dict["name"][i]
            self.__samples[str(fid)] = (code, folder, name)

    def rand_fid(self, code, token: str, db: Session = Depends(get_db)):
        """Get a random image id."""
        if not self.__inited:
            self.init(code)
        fid, user_answers = unique_fid_per_user(token=token, db=db, all_fids=list(self.__samples.keys()), code=code)
        return fid, user_answers

    def get(self, fid, code):
        """Get image information."""
        if not self.__inited:
            self.init(code)
        return self.__samples[fid]

    def mark(self, fid: str, type: str, code: str, token: str, db: Session = Depends(get_db)):
        """Mark an image and update its statistics."""
        if fid is None or len(fid) == 0:
            return
        f = self.__samples.get(fid, None)
        if f is None:
            return

        score = mark_image(db=db, type=type, fid=fid, token=token, code=code)
        self.__answers += 1

        if score:
            # out_dir = Path(self.__out_path) / Path(str(score)) / code
            # os.makedirs(out_dir, exist_ok=True)
            self.__samples.pop(fid)

    def size(self) -> int:
        return len(self.__samples)

    def all(self) -> int:
        return self.__all

    def answers(self) -> int:
        return self.__answers
