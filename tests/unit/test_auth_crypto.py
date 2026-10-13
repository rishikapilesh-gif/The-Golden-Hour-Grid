from backend.app.core.security import (
    hash_password,
    verify_password,
    generate_session_token,
    hash_session_token
)


def test_password_hash_and_verify():
    password = "SuperSecurePassword123!"
    pw_hash = hash_password(password)

    # Must not store plaintext
    assert pw_hash != password
    assert pw_hash.startswith("$argon2id$")

    # Correct password verifies
    assert verify_password(password, pw_hash) is True

    # Wrong password fails
    assert verify_password("WrongPassword!", pw_hash) is False
    assert verify_password("", pw_hash) is False


def test_session_token_generation_and_hashing():
    token1 = generate_session_token()
    token2 = generate_session_token()

    assert token1 != token2
    assert len(token1) >= 32

    hash1 = hash_session_token(token1)
    hash2 = hash_session_token(token2)

    assert hash1 != hash2
    assert hash1 == hash_session_token(token1)
