import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from scans.models import Finding, Scan
from tests.factories import make_org, make_repo, make_user

SECRET_FILE = b'consumer_secret = "abc123XYZ789secretKEY"\nDEBUG = True\n'


@pytest.mark.django_db
def test_upload_scan_save_and_chart(client):
    org = make_org()
    dev = make_user(org, "developer")
    repo = make_repo(org)
    client.force_login(dev)

    response = client.post(reverse("scans:upload"), {
        "repository": repo.pk,
        "files": [SimpleUploadedFile("settings.py", SECRET_FILE)],
    })

    scan = Scan.objects.get()
    assert response.status_code == 302
    assert response["Location"] == reverse("scans:detail", args=[scan.pk])
    codes = set(Finding.objects.values_list("rule_code", flat=True))
    assert {"VCS-001", "PROD-001"} <= codes
    assert scan.total_findings == Finding.objects.count()
    assert all("abc123XYZ789secretKEY" not in f.masked_evidence for f in Finding.objects.all())

    chart = client.get(reverse("dashboard:chart", args=["severity"]))
    assert chart.status_code == 200 and chart.content.startswith(b"\x89PNG")
    home = client.get(reverse("dashboard:home"))
    assert home.status_code == 200 and b"Risk score" in home.content
