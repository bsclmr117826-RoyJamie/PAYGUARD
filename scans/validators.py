import os

ALLOWED_EXTENSIONS = {".py", ".txt", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini", ".env", ".js", ".md"}
MAX_FILE_BYTES = 1_000_000      # same limit as scanner.engine.MAX_FILE_BYTES
MAX_FILES_PER_SCAN = 20
MAX_PATH_LENGTH = 300


def clean_path(raw: str):
    """Safe repository-relative path with forward slashes, or None if unsafe."""
    path = raw.replace("\\", "/").strip()
    parts = [p for p in path.split("/") if p not in ("", ".")]
    if not parts or ".." in parts or "\x00" in path or len(path) > MAX_PATH_LENGTH:
        return None
    return "/".join(parts)


def extension_of(path: str) -> str:
    name = os.path.basename(path).lower()
    if name.startswith(".env"):
        return ".env"
    return os.path.splitext(name)[1]


def validate_upload(path: str, content: bytes) -> list:
    """Return error messages. An empty list means the file is accepted."""
    cleaned = clean_path(path)
    if cleaned is None:
        return ["Unsafe file path."]
    errors = []
    if extension_of(cleaned) not in ALLOWED_EXTENSIONS:
        errors.append("File type not allowed.")
    if not content:
        errors.append("File is empty.")
    if len(content) > MAX_FILE_BYTES:
        errors.append("File is larger than 1 MB.")
    if b"\x00" in content:
        errors.append("Binary files are not accepted.")
    return errors
