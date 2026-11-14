"""Registry pillar: dependency rules (REG-001)."""
import re

from scanner.models import Hit
from scanner.utils import basename

# name==1.2.3  or  name[extra]==1.2.3  (optionally followed by an environment marker)
_PINNED = re.compile(r"^[A-Za-z0-9_.\-]+(\[[A-Za-z0-9_,.\-]+\])?==[0-9][A-Za-z0-9_.!+\-]*(\s*;.*)?$")


def is_requirements(path: str) -> bool:
    name = basename(path)
    return name.startswith("requirements") and name.endswith(".txt")


def check_unpinned_dependencies(text: str) -> list[Hit]:
    """REG-001: any dependency that is not locked to an exact version with ==."""
    hits = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        s = line.split("#")[0].strip().rstrip("\\").strip()
        if not s or s.startswith("-"):      # blank, comment, or option like -r / --hash
            continue
        s = re.sub(r"\s*==\s*", "==", s)
        if not _PINNED.match(s):
            hits.append((line_no, s))
    return hits
