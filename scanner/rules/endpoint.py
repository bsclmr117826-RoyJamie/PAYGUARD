"""Endpoint / IDE pillar: project-level rule (EP-001).

This rule looks at the whole project folder (not one file's text), so the engine
calls check_project() separately from the file-level rules.
"""
import fnmatch
import os

from scanner.models import Hit

CODE = "EP-001"
TITLE = ".env file is not listed in .gitignore"
SEVERITY = "Medium"


def check_project(root: str) -> list[tuple[str, int, str]]:
    """Return [(file_path, line_number, evidence)] when .env exists but is not ignored."""
    env_path = os.path.join(root, ".env")
    if not os.path.isfile(env_path):
        return []

    gitignore_path = os.path.join(root, ".gitignore")
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                pattern = line.strip().lstrip("/")
                if pattern and not pattern.startswith("#") and fnmatch.fnmatch(".env", pattern):
                    return []  # .env is ignored, all good
        return [(".gitignore", 1, ".env exists but is not ignored")]

    return [(".env", 1, ".env exists and there is no .gitignore")]
