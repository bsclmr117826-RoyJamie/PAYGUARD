import pytest

from scans.validators import MAX_FILE_BYTES, clean_path, extension_of, validate_upload


@pytest.mark.parametrize("path,content,expected_fragment", [
    ("tool.exe", b"MZ data", "not allowed"),                        # TC-04: wrong type
    ("big.py", b"x" * (MAX_FILE_BYTES + 1), "larger than 1 MB"),   # TC-04: too large
    ("empty.py", b"", "empty"),
    ("../etc/passwd.py", b"x = 1", "Unsafe"),
    ("blob.py", b"abc\x00def", "Binary"),
])
def test_validate_upload_rejects(path, content, expected_fragment):
    errors = validate_upload(path, content)
    assert errors and any(expected_fragment in e for e in errors)


@pytest.mark.parametrize("path", ["app.py", ".env", ".env.production", "dir/settings.yml", "requirements.txt"])
def test_validate_upload_accepts(path):
    assert validate_upload(path, b"x = 1\n") == []


def test_clean_path_and_extension():
    assert clean_path("a\\b/./c.py") == "a/b/c.py"
    assert clean_path("/abs/x.py") == "abs/x.py"
    assert clean_path("a/../b.py") is None
    assert extension_of(".env.production") == ".env"
    assert extension_of("Dir/App.PY") == ".py"


def test_requirements_are_pinned():
    from pathlib import Path
    lines = Path(__file__).resolve().parents[2].joinpath("requirements.txt").read_text().splitlines()
    for line in lines:
        if line.strip() and not line.startswith("#"):
            assert "==" in line, f"not pinned: {line}"
