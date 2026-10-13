"""Password policy and hashing.

Rules (mirrored for instant feedback in frontend/src/lib/password.js):
at least 12 characters, at most 256, and not a common or easily guessed password.
Hashing uses Werkzeug's salted scrypt (no extra dependency).
"""
from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

MIN_LENGTH = 12
MAX_LENGTH = 256

# Frequently used passwords that pass the length rule (compared case-insensitively).
COMMON = frozenset({
    "password1234", "password12345", "password123456", "passw0rd1234", "123456789012", "1234567890123",
    "12345678901234", "qwertyuiopas", "qwertyuiop123", "qwerty123456", "1qaz2wsx3edc", "iloveyou1234",
    "letmein12345", "welcome12345", "welcome123456", "administrator", "admin1234567", "abc123456789",
    "abcdefghijkl", "aaaaaaaaaaaa", "111111111111", "000000000000", "trustno11234", "football1234",
    "baseball1234", "superman1234", "sunshine1234", "princess1234", "dragon123456", "monkey123456",
    "changeme1234", "smartlab1234", "smartlabai123", "laboratory123", "laboratory1234", "qazwsxedcrfv",
    "zaq12wsxcde3", "asdfghjkl123", "1234qwerasdf", "p@ssw0rd1234", "password!234", "mypassword123",
})
_SEQUENCES = ("01234567890123456789", "abcdefghijklmnopqrstuvwxyz", "qwertyuiopasdfghjklzxcvbnm")

# A real hash used to equalise timing when an email address is unknown.
DUMMY_HASH = generate_password_hash("timing-equaliser-not-a-real-password")


def is_common(password: str, email: str = "", name: str = "") -> bool:
    p = password.lower()
    if p in COMMON or len(set(p)) == 1 or any(p in seq for seq in _SEQUENCES):
        return True
    local = email.lower().split("@")[0]
    if len(local) >= 4 and local in p:
        return True
    first = (name.lower().split() or [""])[0]
    return len(first) >= 4 and "".join(ch for ch in p if ch.isalpha()) == first


def password_problem(password: str, email: str = "", name: str = "") -> str | None:
    """Return a user-facing reason the password is unacceptable, or None."""
    if not isinstance(password, str) or len(password) < MIN_LENGTH:
        return f"Use at least {MIN_LENGTH} characters."
    if len(password) > MAX_LENGTH:
        return f"Use at most {MAX_LENGTH} characters."
    if is_common(password, email, name):
        return "This password is too common or easy to guess. Choose another."
    return None


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(stored_hash: str | None, password: str) -> bool:
    return check_password_hash(stored_hash or DUMMY_HASH, password) and stored_hash is not None
