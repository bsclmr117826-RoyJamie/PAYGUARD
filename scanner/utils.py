"""Small helper functions used by several rules."""
import os

_PLACEHOLDER_MARKERS = ("example", "changeme", "placeholder", "xxxx", "dummy", "<")


def mask(value: str) -> str:
    """Keep only the first 4 characters. Full secrets must never be stored."""
    return value[:4] + "*" * 8


def is_placeholder(value: str) -> bool:
    """True for obvious fake values like 'your-api-key-here', to cut false positives."""
    low = value.lower()
    return low.startswith("your") or any(m in low for m in _PLACEHOLDER_MARKERS)


def normalise_path(path: str) -> str:
    """Use forward slashes everywhere so Windows and Linux paths behave the same."""
    return path.replace("\\", "/")


def basename(path: str) -> str:
    return os.path.basename(normalise_path(path)).lower()
