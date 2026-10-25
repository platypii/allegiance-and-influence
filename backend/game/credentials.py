"""Server-only credential loading. Paths and values never enter game configuration."""

import os
from pathlib import Path


def openrouter_key(path=None):
    """An explicitly selected file takes precedence over the environment value."""
    path = path if path is not None else os.environ.get("OPENROUTER_API_KEY_FILE")
    if path:
        try:
            with Path(path).expanduser().open() as source:
                value = source.read(4097)
        except (OSError, UnicodeError):
            raise ValueError("Cannot read the configured OpenRouter key file") from None
    else:
        value = os.environ.get("OPENROUTER_API_KEY", "")
    value = value.strip()
    if not value:
        return None
    if len(value) > 4096 or any(c.isspace() for c in value):
        raise ValueError("The OpenRouter key must be a single token")
    return value
