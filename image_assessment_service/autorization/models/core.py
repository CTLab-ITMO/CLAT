from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    nickname = Column(String, unique=True)

    items = relationship("Item", back_populates="owner")
    tokens = relationship("Token", back_populates="user")
    image_ratings = relationship("ImageRatings", back_populates="user")


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String, unique=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    # Ensure this matches the attribute in the User model
    user = relationship("User", back_populates="tokens")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Ensure this matches the attribute in the User model
    owner = relationship("User", back_populates="items")


class Images(Base):
    __tablename__ = "images"

    fid = Column(UUID, primary_key=True, index=True)
    grade_1 = Column(Integer, nullable=True, default=0)
    grade_2 = Column(Integer, nullable=True, default=0)
    grade_3 = Column(Integer, nullable=True, default=0)
    grade_4 = Column(Integer, nullable=True, default=0)
    grade_5 = Column(Integer, nullable=True, default=0)
    inappropriate = Column(Integer, nullable=True, default=0)

    code = Column(String, autoincrement=False)
    folder = Column(String, autoincrement=False)
    name = Column(String, autoincrement=False)
    annotated = Column(Boolean, default=False, autoincrement=False)

    # Relationship to image ratings
    image_ratings = relationship(
        "ImageRatings",
        back_populates="image",
        foreign_keys="[ImageRatings.image_fid, ImageRatings.image_code]",
    )

    __table_args__ = (UniqueConstraint("fid", "code", name="uq_image_fid_code"),)


class ImageRatings(Base):
    __tablename__ = "image_ratings"

    # Foreign keys (not part of primary key)
    user_nickname = Column(String, ForeignKey("users.nickname"))
    image_fid = Column(UUID, ForeignKey("images.fid"))
    image_code = Column(String)  # New column for the code

    rating = Column(Integer, nullable=False)

    # Composite foreign key constraint
    __table_args__ = (
        ForeignKeyConstraint(
            ["image_fid", "image_code"],
            ["images.fid", "images.code"],
            name="fk_image_rating",
        ),
    )

    # Relationships
    user = relationship("User", back_populates="image_ratings")
    image = relationship(
        "Images", back_populates="image_ratings", foreign_keys=[image_fid, image_code]
    )

    __table_args__ = (PrimaryKeyConstraint("user_nickname", "image_fid"),)

class Role(Base):
    __tablename__ = "roles"

    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(20))

    __table_args__ = (PrimaryKeyConstraint("user_id", "name"),)


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    annotators_count = Column(Integer)
    days_to_complete = Column(Integer)
    deadline = Column(DateTime)


class Annotation(Base):
    __tablename__ = "annotations"

    annotation_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.task_id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    deadline = Column(DateTime)
    description = Column(String)
