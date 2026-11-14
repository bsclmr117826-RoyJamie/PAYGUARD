from dataclasses import dataclass

from django.core.exceptions import PermissionDenied
from django.db import transaction

from scanner import calculate_risk_score, scan_text
from scanner.rules import ALL_RULES
from scanner.sitf import SITF_MAP

from .models import Finding, RuleSetting, Scan, UploadedFile
from .validators import MAX_FILES_PER_SCAN, clean_path, extension_of, validate_upload


@dataclass(frozen=True)
class UploadItem:
    path: str        # repository-relative, e.g. ".github/workflows/ci.yml" or "settings.py"
    content: bytes


class ScanValidationError(Exception):
    def __init__(self, errors: dict):
        super().__init__("Upload rejected")
        self.errors = errors      # {path: [messages]}; key "" means the whole upload


def active_rules() -> list:
    off = set(RuleSetting.objects.filter(is_active=False).values_list("rule_code", flat=True))
    return [rule for rule in ALL_RULES if rule.code not in off]


def sync_rule_settings() -> None:
    """Make sure every rule code has a RuleSetting row (called by the admin page)."""
    for code in SITF_MAP:
        RuleSetting.objects.get_or_create(rule_code=code)


def save_scan_results(*, user, repository, files, findings) -> Scan:
    """Save one scan, its file metadata and its findings in a single transaction.

    files: list of (path, size_bytes). findings: list of scanner Finding objects.
    """
    with transaction.atomic():
        scan = Scan.objects.create(repository=repository, started_by=user)
        for path, size in files:
            UploadedFile.objects.create(scan=scan, path=path, extension=extension_of(path), size_bytes=size)
        Finding.objects.bulk_create([Finding(scan=scan, **f.to_dict()) for f in findings])
        scan.total_findings = len(findings)
        scan.risk_score = calculate_risk_score(findings)
        scan.save(update_fields=["total_findings", "risk_score"])
        repository.latest_risk_score = scan.risk_score
        repository.save(update_fields=["latest_risk_score"])
    return scan


def run_scan(*, user, repository, uploads: list) -> Scan:
    if user.role != "developer" or repository.organization_id != user.organization_id:
        raise PermissionDenied
    errors = {}
    if not uploads:
        errors[""] = ["Choose at least one file."]
    if len(uploads) > MAX_FILES_PER_SCAN:
        errors[""] = [f"At most {MAX_FILES_PER_SCAN} files per scan."]
    checked = []
    for item in uploads:
        problems = validate_upload(item.path, item.content)
        if problems:
            errors[item.path] = problems
        else:
            checked.append((clean_path(item.path), item.content))
    if errors:
        raise ScanValidationError(errors)        # nothing is saved

    rules = active_rules()
    try:
        found = []
        for path, content in checked:
            found.extend(scan_text(content.decode("utf-8", errors="ignore"), path, rules=rules))
        return save_scan_results(
            user=user, repository=repository,
            files=[(path, len(content)) for path, content in checked], findings=found,
        )
    except Exception:
        Scan.objects.create(repository=repository, started_by=user, status=Scan.Status.FAILED)
        raise
