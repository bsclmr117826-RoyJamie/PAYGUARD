"""Production pillar: risky production settings (PROD-001, PROD-002)."""
import re

from scanner.models import Hit
from scanner.utils import basename

_DEBUG_ON = re.compile(r"^\s*DEBUG\s*=\s*(?:True|true|1)\s*(?:#.*)?$")

# CALLBACK_URL = "http://..."  (ignores localhost addresses)
_HTTP_SETTING = re.compile(
    r"""(?P<key>[A-Za-z_]*(?:url|uri|endpoint|callback|host)[A-Za-z_]*)["']?\s*[=:]\s*["']?(?P<url>http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])[^\s"']+)""",
    re.IGNORECASE,
)

_CONFIG_EXTENSIONS = (".py", ".env", ".yml", ".yaml", ".json", ".cfg", ".ini", ".toml")


def is_debug_file(path: str) -> bool:
    name = basename(path)
    return name.endswith((".py", ".env")) or name.startswith(".env")


def is_config_file(path: str) -> bool:
    name = basename(path)
    return name.endswith(_CONFIG_EXTENSIONS) or name.startswith(".env")


def check_debug_enabled(text: str) -> list[Hit]:
    """PROD-001: DEBUG = True left on."""
    return [
        (line_no, line.strip())
        for line_no, line in enumerate(text.splitlines(), start=1)
        if _DEBUG_ON.match(line)
    ]


def check_http_endpoint(text: str) -> list[Hit]:
    """PROD-002: a URL/endpoint/callback setting that uses http:// instead of https://."""
    hits = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = _HTTP_SETTING.search(line)
        if match:
            # keep the URL without its query string, which could contain a token
            hits.append((line_no, match.group("url").split("?")[0][:80]))
    return hits
