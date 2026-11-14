import csv
import io

import pytest
from django.core import management
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from scanner import calculate_risk_score
from scans.models import Finding, RuleSetting, Scan, UploadedFile
from repos.models import Repository
from tests.factories import make_org, make_repo, make_user

SECRET = b'consumer_secret = "abc123XYZ789secretKEY"\n'


@pytest.fixture
def dev_setup(client, db):
    org = make_org()
    dev, repo = make_user(org, "developer"), make_repo(org)
    client.force_login(dev)
    return client, org, dev, repo


def upload(client, repo, files=(), workflow_files=()):
    return client.post(reverse("scans:upload"), {
        "repository": repo.pk,
        "files": [SimpleUploadedFile(n, c) for n, c in files],
        "workflow_files": [SimpleUploadedFile(n, c) for n, c in workflow_files],
    })


def test_tc04_bad_upload_is_rejected_and_nothing_is_saved(dev_setup):
    client, org, dev, repo = dev_setup
    response = upload(client, repo, files=[("tool.exe", b"MZ")])
    assert response.status_code == 400 and b"not allowed" in response.content
    assert Scan.objects.count() == 0 and Finding.objects.count() == 0


def test_oversized_file_is_rejected_without_a_scan(dev_setup):
    client, org, dev, repo = dev_setup
    response = upload(client, repo, files=[("big.py", b"x" * 1_000_001)])
    assert response.status_code == 400 and Scan.objects.count() == 0


def test_tc11_scan_is_saved_with_findings_score_and_metadata_only(dev_setup):
    client, org, dev, repo = dev_setup
    upload(client, repo, files=[("a.py", SECRET), ("b.py", SECRET)])
    scan = Scan.objects.get()
    assert scan.status == "complete" and scan.total_findings == 2
    assert scan.risk_score == calculate_risk_score(scan.findings.all())
    repo.refresh_from_db()
    assert repo.latest_risk_score == scan.risk_score
    files = UploadedFile.objects.filter(scan=scan)
    assert sorted(f.path for f in files) == ["a.py", "b.py"] and files[0].size_bytes == len(SECRET)
    stored = " ".join(f.masked_evidence for f in scan.findings.all())
    assert "abc123XYZ789secretKEY" not in stored and "abc1" in stored    # first 4 characters only


def test_workflow_files_get_the_workflows_path_so_cicd_rules_fire(dev_setup):
    client, org, dev, repo = dev_setup
    upload(client, repo, workflow_files=[("ci.yml", b"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@main\n")])
    finding = Finding.objects.get(rule_code="CICD-001")
    assert finding.file_path == ".github/workflows/ci.yml"


def test_tc12_admin_can_switch_a_rule_off(dev_setup):
    client, org, dev, repo = dev_setup
    RuleSetting.objects.create(rule_code="VCS-001", is_active=False)
    upload(client, repo, files=[("a.py", SECRET)])
    assert not Finding.objects.filter(rule_code="VCS-001").exists()


def test_admin_rule_settings_page_creates_a_row_for_every_rule(client, db):
    admin = make_user(make_org(), "admin")
    client.force_login(admin)
    assert client.get("/admin/scans/rulesetting/").status_code == 200
    assert RuleSetting.objects.count() >= 10


def test_tc15_developer_registers_repository_in_own_organisation(dev_setup):
    client, org, dev, repo = dev_setup
    response = client.post(reverse("repos:create"), {"name": "wallet-service", "url": "https://example.com/r"})
    assert response.status_code == 302
    created = Repository.objects.get(name="wallet-service")
    assert created.organization == org and created.created_by == dev
    duplicate = client.post(reverse("repos:create"), {"name": "wallet-service", "url": ""})
    assert duplicate.status_code == 200 and b"already has" in duplicate.content


def test_tc16_developer_updates_finding_status_and_bad_value_is_ignored(dev_setup):
    client, org, dev, repo = dev_setup
    upload(client, repo, files=[("a.py", SECRET)])
    scan, finding = Scan.objects.get(), Finding.objects.get()
    url = reverse("scans:finding_status", args=[scan.pk, finding.pk])
    client.post(url, {"status": "accepted-risk"})
    finding.refresh_from_db()
    assert finding.status == "accepted-risk"
    client.post(url, {"status": "not-a-status"})
    finding.refresh_from_db()
    assert finding.status == "accepted-risk"


def test_tc14_auditor_exports_masked_csv_and_developer_cannot(client, db):
    org = make_org()
    dev, auditor, repo = make_user(org, "developer"), make_user(org, "auditor"), make_repo(org)
    scan = Scan.objects.create(repository=repo, started_by=dev)
    for i, evidence in enumerate(["abc1********", "=HYPERLINK(1)", "plain"]):
        Finding.objects.create(scan=scan, rule_code="VCS-001", title="t", severity="Critical", pillar="VCS",
                               technique="x", file_path="a.py", line_number=i + 1, masked_evidence=evidence)
    client.force_login(dev)
    assert client.get(reverse("scans:export", args=[scan.pk])).status_code == 403
    client.force_login(auditor)
    response = client.get(reverse("scans:export", args=[scan.pk]))
    assert response.status_code == 200 and response["Content-Type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(response.content.decode())))
    assert rows[0][0] == "rule_code" and len(rows) == 4
    assert "'=HYPERLINK(1)" in [r[7] for r in rows]          # formula injection neutralised


def test_finding_text_is_escaped(client, db):
    org = make_org()
    dev, repo = make_user(org, "developer"), make_repo(org)
    scan = Scan.objects.create(repository=repo, started_by=dev)
    Finding.objects.create(scan=scan, rule_code="VCS-001", title="t", severity="Critical", pillar="VCS", technique="x",
                           file_path="<script>alert(1)</script>.py", line_number=1, masked_evidence="<img src=x onerror=alert(1)>")
    client.force_login(dev)
    html = client.get(reverse("scans:detail", args=[scan.pk])).content.decode()
    assert "<script>alert(1)" not in html and "<img src=x" not in html
    assert "&lt;script&gt;" in html and "&lt;img src=x" in html


def test_scan_folder_command_evaluates_ep001(db, tmp_path):
    org = make_org()
    dev, repo = make_user(org, "developer"), make_repo(org)
    (tmp_path / ".env").write_text("TOKEN=abc\n")
    management.call_command("scan_folder", str(repo.pk), str(tmp_path), "--username", dev.username)
    assert Finding.objects.filter(rule_code="EP-001").exists()


def test_failed_scan_is_recorded_when_scanning_crashes(dev_setup, monkeypatch):
    client, org, dev, repo = dev_setup
    import scans.services as services

    def boom(*args, **kwargs):
        raise RuntimeError("scanner crashed")

    monkeypatch.setattr(services, "scan_text", boom)
    with pytest.raises(RuntimeError):
        upload(client, repo, files=[("a.py", SECRET)])
    assert Scan.objects.get().status == "failed" and Finding.objects.count() == 0
