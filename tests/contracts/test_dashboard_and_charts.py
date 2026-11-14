import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

import charts.render as render
from dashboard.services import build_dashboard_data
from tests.factories import make_org, make_repo, make_user

KEYS = {"repository", "latest_scan", "severity_counts", "pillar_counts", "trend", "top_rules"}
SEVERITIES = {"Critical", "High", "Medium", "Low"}
PILLARS = {"Endpoint / IDE", "VCS", "CI/CD", "Registry", "Production"}


@pytest.mark.django_db
def test_dashboard_data_has_every_key_when_empty():
    dev = make_user(make_org())
    data = build_dashboard_data(dev)
    assert set(data) == KEYS
    assert data["repository"] is None and data["latest_scan"] is None
    assert data["trend"] == [] and data["top_rules"] == []
    assert set(data["severity_counts"]) == SEVERITIES and not any(data["severity_counts"].values())
    assert set(data["pillar_counts"]) == PILLARS


@pytest.mark.django_db
def test_dashboard_data_has_every_key_with_data(client):
    org = make_org()
    dev, repo = make_user(org), make_repo(org)
    client.force_login(dev)
    client.post(reverse("scans:upload"), {
        "repository": repo.pk,
        "files": [SimpleUploadedFile("leaked.py", b'consumer_secret = "abc123XYZ789secretKEY"\n')],
    })
    data = build_dashboard_data(dev)
    assert set(data) == KEYS
    assert data["repository"] == {"id": repo.pk, "name": "payments-api"}
    assert data["severity_counts"]["Critical"] == 1
    assert data["pillar_counts"]["VCS"] == 1
    assert data["latest_scan"]["total_findings"] == 1
    assert len(data["trend"]) == 1 and data["top_rules"] == [["VCS-001", 1]]


@pytest.mark.parametrize("fn,arg", [
    (render.severity_chart, {}), (render.severity_chart, {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}),
    (render.pillar_chart, {}), (render.pillar_chart, {"VCS": 0, "CI/CD": 0}),
    (render.trend_chart, []), (render.top_rules_chart, []),
])
def test_charts_return_png_for_empty_and_zero_input(fn, arg):
    assert fn(arg).startswith(b"\x89PNG")


def test_chart_size_is_640_by_360():
    import struct
    png = render.severity_chart({"Critical": 1, "High": 0, "Medium": 0, "Low": 0})
    width, height = struct.unpack(">II", png[16:24])
    assert (width, height) == (640, 360)


@pytest.mark.django_db
def test_chart_view_unknown_kind_is_404(client):
    client.force_login(make_user(make_org()))
    assert client.get("/dashboard/charts/nonsense.png").status_code == 404
