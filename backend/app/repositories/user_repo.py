from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.session import SessionModel


class UserRepository:
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username.strip().lower()).first()

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        password_hash: str,
        role: str,
        hospital_id: Optional[str] = None
    ) -> User:
        user = User(
            username=username.strip().lower(),
            password_hash=password_hash,
            role=role,
            hospital_id=hospital_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_session(
        db: Session,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SessionModel:
        session = SessionModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_active_session_by_hash(db: Session, token_hash: str) -> Optional[SessionModel]:
        now = datetime.now(timezone.utc)
        return db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash,
            SessionModel.revoked_at.is_(None),
            SessionModel.expires_at > now
        ).first()

    @staticmethod
    def touch_session(db: Session, session: SessionModel) -> None:
        session.last_seen_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def revoke_session(db: Session, token_hash: str) -> bool:
        session = db.query(SessionModel).filter(SessionModel.token_hash == token_hash).first()
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False
