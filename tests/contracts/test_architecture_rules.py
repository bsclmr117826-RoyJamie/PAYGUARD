"""Enforces the dependency rules in section 3.3 of the design document."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = {"config", "accounts", "repos", "scans", "dashboard", "charts", "scanner", "django"}


def imports_of(folder):
    names = set()
    for path in (ROOT / folder).rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(node.module.split(".")[0])
    return names


def test_scanner_is_framework_free():
    assert not imports_of("scanner") & (PROJECT - {"scanner"})


def test_charts_are_framework_free():
    assert not imports_of("charts") & (PROJECT - {"charts"})


def test_charts_do_not_use_pyplot():
    for path in (ROOT / "charts").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                assert not any("pyplot" in a.name for a in node.names), path
            elif isinstance(node, ast.ImportFrom):
                assert "pyplot" not in (node.module or "") and not any("pyplot" in a.name for a in node.names), path


def test_models_do_not_import_upper_layers():
    for path in ROOT.glob("*/models.py"):
        text = path.read_text(encoding="utf-8")
        for word in ("services", "selectors", "views", "dashboard"):
            assert f"import {word}" not in text and f"from .{word}" not in text, (path, word)


def test_views_do_not_query_the_database():
    for path in ROOT.glob("*/views.py"):
        assert ".objects." not in path.read_text(encoding="utf-8"), path


def test_only_scan_services_calls_scan_text():
    for path in ROOT.glob("*/*.py"):
        if path.parts[-2] in ("scanner", "tests") or path.name == "services.py" and path.parts[-2] == "scans":
            continue
        assert "scan_text(" not in path.read_text(encoding="utf-8"), path
