"""Unit tests for auth utility functions."""

import pytest
from racing_coach_server.auth.utils import (
    generate_device_code,
    generate_session_token,
    generate_user_code,
    hash_password,
    hash_token,
    needs_rehash,
    verify_password,
)


@pytest.mark.unit
class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_hash(self) -> None:
        """Test that hash_password returns a hash string."""
        password = "mysecretpassword"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$argon2id$")

    def test_hash_password_different_each_time(self) -> None:
        """Test that hashing the same password twice produces different hashes (due to salt)."""
        password = "mysecretpassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self) -> None:
        """Test that verify_password returns True for correct password."""
        password = "mysecretpassword"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """Test that verify_password returns False for incorrect password."""
        password = "mysecretpassword"
        hashed = hash_password(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty_password(self) -> None:
        """Test that verify_password handles empty passwords."""
        hashed = hash_password("somepassword")

        assert verify_password("", hashed) is False

    def test_needs_rehash_fresh_hash(self) -> None:
        """Test that a fresh hash doesn't need rehashing."""
        password = "mysecretpassword"
        hashed = hash_password(password)

        assert needs_rehash(hashed) is False


@pytest.mark.unit
class TestTokenGeneration:
    """Tests for token generation functions."""

    def test_generate_session_token_length(self) -> None:
        """Test that session tokens have appropriate length."""
        token = generate_session_token()

        assert token is not None
        assert isinstance(token, str)
        # 32 bytes base64 encoded = ~43 characters
        assert len(token) >= 40

    def test_generate_session_token_unique(self) -> None:
        """Test that session tokens are unique."""
        tokens = {generate_session_token() for _ in range(100)}

        assert len(tokens) == 100

    def test_generate_session_token_url_safe(self) -> None:
        """Test that session tokens are URL-safe."""
        token = generate_session_token()

        # URL-safe base64 uses only alphanumeric, hyphen, and underscore
        assert all(c.isalnum() or c in "-_" for c in token)

    def test_hash_token_consistent(self) -> None:
        """Test that hashing the same token produces the same hash."""
        token = "mytoken123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)

        assert hash1 == hash2

    def test_hash_token_different_tokens(self) -> None:
        """Test that different tokens produce different hashes."""
        token1 = "token1"
        token2 = "token2"

        assert hash_token(token1) != hash_token(token2)

    def test_hash_token_is_sha256(self) -> None:
        """Test that hash_token produces a SHA-256 hex digest."""
        token = "mytoken"
        hashed = hash_token(token)

        # SHA-256 produces 64 hex characters
        assert len(hashed) == 64
        assert all(c in "0123456789abcdef" for c in hashed)


@pytest.mark.unit
class TestDeviceCodeGeneration:
    """Tests for device code generation functions."""

    def test_generate_device_code_length(self) -> None:
        """Test that device codes have appropriate length."""
        code = generate_device_code()

        assert code is not None
        assert isinstance(code, str)
        assert len(code) >= 40

    def test_generate_device_code_unique(self) -> None:
        """Test that device codes are unique."""
        codes = {generate_device_code() for _ in range(100)}

        assert len(codes) == 100

    def test_generate_user_code_length(self) -> None:
        """Test that user codes are 8 characters."""
        code = generate_user_code()

        assert len(code) == 8

    def test_generate_user_code_uppercase(self) -> None:
        """Test that user codes are uppercase."""
        code = generate_user_code()

        assert code == code.upper()

    def test_generate_user_code_no_confusing_chars(self) -> None:
        """Test that user codes don't contain confusing characters."""
        confusing = "0OI1L"

        for _ in range(100):
            code = generate_user_code()
            assert not any(c in confusing for c in code)

    def test_generate_user_code_unique(self) -> None:
        """Test that user codes are unique (statistically)."""
        codes = {generate_user_code() for _ in range(100)}

        # Should have very high uniqueness
        assert len(codes) >= 99
