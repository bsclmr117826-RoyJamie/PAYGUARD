"""CI/CD pillar: GitHub Actions workflow rules (CICD-001, CICD-002, CICD-003)."""
import re

import yaml

from scanner.models import Hit
from scanner.utils import normalise_path

_USES = re.compile(r"^\s*-?\s*uses:\s*(?P<action>[^@\s]+)@(?P<ref>[^\s#]+)")
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_WRITE_ALL = re.compile(r"^\s*permissions:\s*write-all\s*(#.*)?$")
_UNTRUSTED_MARKERS = ("github.event.pull_request.head", "github.head_ref")


def is_workflow(path: str) -> bool:
    """True for files inside .github/workflows/ ending in .yml or .yaml."""
    p = "/" + normalise_path(path).lstrip("/")
    return "/.github/workflows/" in p and p.lower().endswith((".yml", ".yaml"))


def check_unpinned_actions(text: str) -> list[Hit]:
    """CICD-001: `uses: owner/action@main` instead of a full 40-character commit SHA."""
    hits = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = _USES.match(line)
        if not match:
            continue  # local actions (./path) have no @ and are skipped
        ref = match.group("ref")
        if _FULL_SHA.match(ref) or ref.startswith("sha256:"):
            continue  # pinned
        hits.append((line_no, line.strip()))
    return hits


def _has_trigger(triggers, name: str) -> bool:
    if isinstance(triggers, str):
        return triggers == name
    if isinstance(triggers, list):
        return name in triggers
    if isinstance(triggers, dict):
        return name in triggers
    return False


def check_pull_request_target(text: str) -> list[Hit]:
    """CICD-002: pull_request_target trigger that also uses code from the pull request.

    Narrow on purpose (fewer false positives): flags only when the workflow uses the
    pull_request_target trigger AND refers to the untrusted PR head.
    """
    try:
        data = yaml.safe_load(text)          # safe_load only, never yaml.load
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []
    # Gotcha: PyYAML reads the key `on` as the boolean True, so check both.
    triggers = data.get("on", data.get(True))
    if not _has_trigger(triggers, "pull_request_target"):
        return []
    if not any(marker in text for marker in _UNTRUSTED_MARKERS):
        return []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if "pull_request_target" in line:
            return [(line_no, line.strip())]
    return [(1, "pull_request_target")]


def check_write_all_permissions(text: str) -> list[Hit]:
    """CICD-003: `permissions: write-all` gives the pipeline token far too much power."""
    return [
        (line_no, line.strip())
        for line_no, line in enumerate(text.splitlines(), start=1)
        if _WRITE_ALL.match(line)
    ]
