"""Validate external links exposed as project data."""

from urllib.parse import parse_qsl, urlsplit


def safe_url(value: object) -> str | None:
    candidate = value.strip() if isinstance(value, str) else None
    if not candidate or any(
        char.isspace() or ord(char) < 32 or char == "\\" for char in candidate
    ):
        return None
    try:
        parsed = urlsplit(candidate)
        if (
            parsed.scheme not in ("https", "http")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or any(key.lower() == "api_key" for key, _ in parse_qsl(parsed.query))
        ):
            return None
        parsed.port  # Reject malformed ports without exposing the supplied URL.
    except ValueError:
        return None
    return candidate
