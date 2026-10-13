from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.security import verify_password, generate_session_token, hash_session_token
from backend.app.models.user import User
from backend.app.models.session import SessionModel
from backend.app.repositories.user_repo import UserRepository


class AuthService:
    @staticmethod
    def authenticate_user(
        db: Session,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Tuple[User, str]]:
        user = UserRepository.get_by_username(db, username)
        if not user or not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        # Create session
        token = generate_session_token()
        token_hash = hash_session_token(token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.SESSION_TTL_MINUTES)

        UserRepository.create_session(
            db=db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return user, token

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        if not token:
            return None
        token_hash = hash_session_token(token)
        session_model = UserRepository.get_active_session_by_hash(db, token_hash)
        if not session_model:
            return None

        # Touch session
        UserRepository.touch_session(db, session_model)
        return session_model.user

    @staticmethod
    def logout(db: Session, token: str) -> bool:
        if not token:
            return False
        token_hash = hash_session_token(token)
        return UserRepository.revoke_session(db, token_hash)
