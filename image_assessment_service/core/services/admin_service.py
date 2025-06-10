from typing import List

from fastapi import HTTPException
from image_assessment_service.autorization.models.core import Role, User

AVAILABLE_ROLES = ["admin", "teacher"]


class AdminServiceImpl:
    def __init__(self, db_session):
        self.db_session = db_session

    async def get_user_roles(self, user_id) -> List[Role]:
        with self.db_session() as db:
            roles = db.query(Role).filter(Role.user_id == user_id).all()
            return roles

    async def get_users(self):
        with self.db_session() as db:
            users = db.query(User).all()
            return users

    async def get_users_with_roles(self):
        users = await self.get_users()
        for user in users:
            user.roles = [r.name for r in await self.get_user_roles(user.id)]
            del user.hashed_password

        return users

    async def add_role(self, user_id: str, role: str):
        with self.db_session() as db:
            target_user = db.query(User).filter(User.id == user_id).first()

            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")

            if role not in AVAILABLE_ROLES:
                raise HTTPException(status_code=400, detail="Invalid role")

            existing_role = (
                db.query(Role)
                .filter(Role.user_id == user_id, Role.name == role)
                .first()
            )

            if not existing_role:
                new_role = Role(user_id=user_id, name=role)
                db.add(new_role)
                db.commit()

    async def remove_role(self, user_id: str, role: str):
        with self.db_session() as db:
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                raise HTTPException(status_code=404, detail="User or role not found")

            db.query(Role).filter(Role.user_id == user_id, Role.name == role).delete()
            db.commit()
