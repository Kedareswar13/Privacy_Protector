import hashlib
import hmac
import os
from typing import Any


def _get_salt() -> bytes:
    salt = os.getenv("PSEUDONYM_SALT", "local_dev_salt_any_string")
    return salt.encode("utf-8")


def pseudonymize_identifier(value: str) -> str:
    """Return a stable pseudonym for a given identifier using HMAC-SHA256.

    This does not store any mapping; it just produces a deterministic token
    that can be used as [USER_x] or similar.
    """

    if not value:
        return ""
    digest = hmac.new(_get_salt(), value.encode("utf-8"), hashlib.sha256).hexdigest()
    # Shorten for readability
    return f"USER_{digest[:10]}"


def pseudonymize_text(text: str) -> str:
    """Placeholder: in future, replace raw identifiers inside text.

    For now, this just returns the original text.
    """

    return text
