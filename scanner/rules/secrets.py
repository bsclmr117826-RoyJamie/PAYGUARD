"""VCS pillar: hardcoded secrets (VCS-001, VCS-002, VCS-003). These are the MVP rules."""
import re

from scanner.models import Hit
from scanner.utils import is_placeholder, mask

# consumer_key = "abc..."  /  "consumer_secret": "abc..."  /  daraja_secret = "abc..."
_CONSUMER = re.compile(
    r"""(?:consumer[_-]?key|consumer[_-]?secret|daraja[_-]?key|daraja[_-]?secret)["']?\s*[=:]\s*["'](?P<value>[A-Za-z0-9]{8,})["']""",
    re.IGNORECASE,
)

# passkey = "..."  (Daraja Lipa na M-Pesa passkey)
_PASSKEY = re.compile(
    r"""pass[_-]?key["']?\s*[=:]\s*["'](?P<value>[A-Za-z0-9]{16,})["']""",
    re.IGNORECASE,
)

# GitHub personal access tokens, e.g. ghp_xxxxxxxx...
_GITHUB_TOKEN = re.compile(r"(?P<value>gh[pousr]_[A-Za-z0-9]{36,})")

# api_key / access_token / SECRET_KEY etc. assigned a quoted literal value
_GENERIC = re.compile(
    r"""(?:api[_-]?key|api[_-]?token|access[_-]?token|auth[_-]?token|secret[_-]?key)["']?\s*[=:]\s*["'](?P<value>[A-Za-z0-9_\-+/=.]{12,})["']""",
    re.IGNORECASE,
)


def _scan(text: str, patterns) -> list[Hit]:
    """Return one hit per line; the evidence is always the MASKED value."""
    hits = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            match = pattern.search(line)
            if match and not is_placeholder(match.group("value")):
                hits.append((line_no, mask(match.group("value"))))
                break
    return hits


def check_daraja_consumer(text: str) -> list[Hit]:
    return _scan(text, [_CONSUMER])


def check_daraja_passkey(text: str) -> list[Hit]:
    return _scan(text, [_PASSKEY])


def check_hardcoded_token(text: str) -> list[Hit]:
    return _scan(text, [_GITHUB_TOKEN, _GENERIC])
