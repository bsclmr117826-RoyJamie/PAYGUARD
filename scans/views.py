import csv

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.text import get_valid_filename

from accounts.permissions import ADMIN, AUDITOR, DEVELOPER, role_required

from .forms import UploadForm
from .models import Finding
from .selectors import findings_for_scan, get_finding_in_scan, get_scan_for_user
from .services import ScanValidationError, UploadItem, run_scan
from .validators import MAX_FILE_BYTES, MAX_FILES_PER_SCAN

WORKFLOW_PREFIX = ".github/workflows/"


def _collect(request):
    """Turn uploaded files into UploadItems. Oversized files are reported, never read."""
    uploads, errors = [], {}
    groups = (("files", ""), ("workflow_files", WORKFLOW_PREFIX))
    if sum(len(request.FILES.getlist(name)) for name, _ in groups) > MAX_FILES_PER_SCAN:
        return [], {"": [f"At most {MAX_FILES_PER_SCAN} files per scan."]}
    for field, prefix in groups:
        for uploaded in request.FILES.getlist(field):
            path = prefix + uploaded.name
            if uploaded.size > MAX_FILE_BYTES:
                errors[path] = ["File is larger than 1 MB."]
            else:
                uploads.append(UploadItem(path=path, content=uploaded.read()))
    return uploads, errors


@role_required(DEVELOPER)
def upload(request):
    form = UploadForm(request.POST or None, user=request.user)
    errors = {}
    if request.method == "POST" and form.is_valid():
        uploads, errors = _collect(request)
        if not errors:
            try:
                scan = run_scan(user=request.user, repository=form.cleaned_data["repository"], uploads=uploads)
            except ScanValidationError as exc:
                errors = exc.errors
            else:
                return redirect("scans:detail", scan_id=scan.pk)
    status = 400 if errors else 200
    return render(request, "scans/upload.html", {"form": form, "errors": errors}, status=status)


@role_required(DEVELOPER, AUDITOR, ADMIN)
def detail(request, scan_id):
    scan = get_scan_for_user(request.user, scan_id)
    role = request.user.role
    return render(request, "scans/detail.html", {
        "scan": scan,
        "findings": findings_for_scan(scan),
        "can_update_status": role in (DEVELOPER, ADMIN),
        "can_export": role in (AUDITOR, ADMIN),
        "status_choices": Finding.Status.choices,
    })


@role_required(DEVELOPER, ADMIN)
def finding_status(request, scan_id, finding_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    scan = get_scan_for_user(request.user, scan_id)
    finding = get_finding_in_scan(scan, finding_id)
    new_status = request.POST.get("status", "")
    if new_status in Finding.Status.values:
        finding.status = new_status
        finding.save(update_fields=["status"])
    return redirect("scans:detail", scan_id=scan.pk)


def _safe_cell(value):
    """Stop spreadsheet formula injection: cells starting with = + - @ are prefixed."""
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


@role_required(AUDITOR, ADMIN)
def export_csv(request, scan_id):
    scan = get_scan_for_user(request.user, scan_id)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{get_valid_filename(f"payguard-scan-{scan.pk}")}.csv"'
    writer = csv.writer(response)
    writer.writerow(["rule_code", "title", "severity", "pillar", "technique", "file_path", "line_number", "masked_evidence", "status"])
    for f in findings_for_scan(scan):
        writer.writerow([_safe_cell(v) for v in (
            f.rule_code, f.title, f.severity, f.pillar, f.technique, f.file_path, f.line_number, f.masked_evidence, f.status)])
    return response
