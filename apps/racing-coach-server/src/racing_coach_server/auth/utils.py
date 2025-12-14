"""Utility functions for authentication."""

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2id hasher with secure defaults (OWASP recommended)
_password_hasher = PasswordHasher(
    time_cost=3,  # Number of iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,  # Number of parallel threads
    hash_len=32,  # Length of the hash
    salt_len=16,  # Length of random salt
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Args:
        password: The plaintext password to hash.

    Returns:
        The hashed password string.
    """
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash.

    Args:
        password: The plaintext password to verify.
        password_hash: The hash to verify against.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        _password_hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def needs_rehash(password_hash: str) -> bool:
    """Check if password hash needs to be rehashed (e.g., after parameter changes).

    Args:
        password_hash: The hash to check.

    Returns:
        True if the hash should be regenerated with current parameters.
    """
    return _password_hasher.check_needs_rehash(password_hash)


def generate_session_token() -> str:
    """Generate a cryptographically secure session token.

    Returns:
        A URL-safe base64-encoded token with 256 bits of entropy.
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a session/device token for storage.

    Tokens are stored as SHA-256 hashes to prevent exposure if the database
    is compromised. The original token is only known to the client.

    Args:
        token: The raw token to hash.

    Returns:
        The SHA-256 hash of the token as a hex string.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_device_code() -> str:
    """Generate a device code for OAuth device flow.

    Returns:
        A URL-safe base64-encoded code with 256 bits of entropy.
    """
    return secrets.token_urlsafe(32)


def generate_user_code() -> str:
    """Generate a user-friendly code for OAuth device flow.

    Generates an 8-character alphanumeric code using characters that are
    easy to read and distinguish (excluding 0, O, I, 1, L).

    Returns:
        An 8-character uppercase alphanumeric code.
    """
    # Use uppercase letters and digits, excluding confusing characters
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(8))
