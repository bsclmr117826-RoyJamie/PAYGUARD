from django.shortcuts import get_object_or_404

from .models import Scan


def scans_for_user(user):
    qs = Scan.objects.filter(repository__organization=user.organization).select_related("repository", "started_by")
    return qs.filter(started_by=user) if user.role == "developer" else qs


def get_scan_for_user(user, scan_id):
    """404 if the scan is not visible to this user."""
    return get_object_or_404(scans_for_user(user), pk=scan_id)


def findings_for_scan(scan):
    """List, Critical first, then by file and line."""
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    return sorted(scan.findings.all(), key=lambda f: (order[f.severity], f.file_path, f.line_number))


def get_finding_in_scan(scan, finding_id):
    return get_object_or_404(scan.findings, pk=finding_id)
