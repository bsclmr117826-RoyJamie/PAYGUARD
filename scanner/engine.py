"""Rule engine: runs the rules over text, files or a whole folder.

Safety: this module only READS text. It never executes, imports or evaluates
anything from the files it scans.
"""
import os

from scanner.models import Finding
from scanner.rules import ALL_RULES, endpoint
from scanner.sitf import map_rule
from scanner.utils import normalise_path

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", ".idea", ".vscode", "staticfiles"}
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".tar", ".exe",
    ".dll", ".so", ".pyc", ".woff", ".woff2", ".ttf", ".mp3", ".mp4", ".sqlite3", ".db",
}
MAX_FILE_BYTES = 1_000_000   # skip files over 1 MB


def scan_text(text: str, file_path: str, rules=None) -> list[Finding]:
    """Run every rule that applies to `file_path` over `text` and return Findings.

    This is the main function the Django upload view should call.
    """
    rules = ALL_RULES if rules is None else rules
    path = normalise_path(file_path)
    findings = []
    for rule in rules:
        if not rule.applies_to(path):
            continue
        pillar, technique = map_rule(rule.code)
        for line_no, evidence in rule.check(text):
            findings.append(Finding(
                rule_code=rule.code,
                title=rule.title,
                severity=rule.severity,
                pillar=pillar,
                technique=technique,
                file_path=path,
                line_number=line_no,
                masked_evidence=evidence[:100],
            ))
    return findings


def scan_file(full_path: str, display_path: str | None = None) -> list[Finding]:
    """Read one file as text and scan it. Returns [] for binary or oversized files."""
    if os.path.splitext(full_path)[1].lower() in SKIP_EXTENSIONS:
        return []
    try:
        if os.path.getsize(full_path) > MAX_FILE_BYTES:
            return []
        with open(full_path, encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
    except OSError:
        return []
    if "\x00" in text:        # binary content
        return []
    return scan_text(text, display_path or full_path)


def scan_directory(root: str) -> list[Finding]:
    """Scan every text file under `root` (a repository folder) plus project-level rules."""
    findings = []
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]   # prune in place
        for name in files:
            full = os.path.join(current, name)
            relative = os.path.relpath(full, root)
            findings.extend(scan_file(full, relative))

    pillar, technique = map_rule(endpoint.CODE)
    for file_path, line_no, evidence in endpoint.check_project(root):
        findings.append(Finding(
            rule_code=endpoint.CODE, title=endpoint.TITLE, severity=endpoint.SEVERITY,
            pillar=pillar, technique=technique, file_path=file_path,
            line_number=line_no, masked_evidence=evidence,
        ))
    return findings
