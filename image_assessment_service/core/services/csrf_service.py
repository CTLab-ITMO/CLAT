import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from image_assessment_service.autorization.models.core import CSRF


class CSRFTokenService:
    """Simple database-driven CSRF token service"""

    __ONE_HOUR_TTL = 3600
    __TOKEN_LEN = 64

    def __init__(self, db: Session):
        self.db = db
        self.token_ttl = self.__ONE_HOUR_TTL

    def create_token(
            self,
            session_id: str,
            purpose: CSRF.Purpose = CSRF.Purpose.GENERAL,
            expires_in: Optional[int] = None
    ) -> str:
        token = self.generate_token()
        csrf_record = self._build_record(token, session_id, purpose, expires_in)

        self._save(csrf_record)

        return token

    def validate_token(
            self,
            token: str,
            session_id: str,
            purpose: Optional[str] = None,
            require_unused: bool = True
    ) -> bool:
        if not token or not session_id:
            return False

        query = self._build_validation_query(token, session_id, purpose, require_unused)

        return bool(query.first())

    def use_token(
            self,
            token: str,
            session_id: str,
            purpose: Optional[str] = None
    ) -> bool:
        if not self.validate_token(token, session_id, purpose, require_unused=True):
            return False

        csrf_record = self._find_record(token, session_id, purpose)
        if not csrf_record or csrf_record.used_at:
            return False

        self._mark_used(csrf_record)

        return True

    def generate_token(self) -> str:
        return secrets.token_urlsafe(self.__TOKEN_LEN)

    def _build_record(
            self,
            token: str,
            session_id: str,
            purpose: CSRF.Purpose,
            expires_in: Optional[int]
    ):
        ttl = expires_in or self.token_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        return CSRF(
            token=token,
            session_id=session_id,
            purpose=purpose.value,
            expires_at=expires_at
        )

    def _save(self, csrf_record) -> None:
        self.db.add(csrf_record)
        self.db.commit()

    def _build_validation_query(self, token, session_id, purpose, require_unused):
        query = self.db.query(CSRF).filter(
            CSRF.token == token,
            CSRF.session_id == session_id,
            CSRF.expires_at > datetime.utcnow()
        )

        if purpose:
            query = query.filter(CSRF.purpose == purpose)
        if require_unused:
            query = query.filter(CSRF.used_at.is_(None))

        return query

    def _find_record(self, token, session_id, purpose):
        query = self.db.query(CSRF).filter(
            CSRF.token == token,
            CSRF.session_id == session_id
        )

        if purpose:
            query = query.filter(CSRF.purpose == purpose)

        return query.first()

    def _mark_used(self, csrf_record) -> None:
        csrf_record.used_at = datetime.utcnow()
        self.db.commit()