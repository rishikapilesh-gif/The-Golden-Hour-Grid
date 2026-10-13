import hashlib
import secrets
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# Configure Argon2id password hasher
_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    type=Type.ID
)


def hash_password(password: str) -> str:
    """Hash plaintext password using Argon2id."""
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def generate_session_token() -> str:
    """Generate an opaque random session token to place in the HttpOnly cookie."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Hash the session token using SHA-256 for safe database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
