"""TC-06: roles and organisations are enforced."""
import pytest
from django.test import Client
from django.urls import reverse

from scans.models import Scan
from tests.factories import make_org, make_repo, make_user


@pytest.fixture
def world(db):
    org_a, org_b = make_org("Org A"), make_org("Org B")
    dev_a, dev_a2 = make_user(org_a, "developer", "dev-a"), make_user(org_a, "developer", "dev-a2")
    return {
        "org_a": org_a, "org_b": org_b, "dev_a": dev_a, "dev_a2": dev_a2,
        "auditor_a": make_user(org_a, "auditor", "aud-a"), "admin_a": make_user(org_a, "admin", "adm-a"),
        "dev_b": make_user(org_b, "developer", "dev-b"),
        "repo_a": make_repo(org_a), "repo_b": make_repo(org_b),
    }


def scan_for(world, repo_key, user_key):
    return Scan.objects.create(repository=world[repo_key], started_by=world[user_key])


@pytest.mark.parametrize("url", [
    "/dashboard/", "/dashboard/charts/severity.png", "/repos/", "/repos/new/", "/scans/new/", "/scans/1/",
])
def test_tc06a_anonymous_is_sent_to_login(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))


def test_tc06b_developer_cannot_use_admin_site(client, world):
    client.force_login(world["dev_a"])
    response = client.get("/admin/")
    assert response.status_code == 302 and "/admin/login/" in response["Location"]


def test_tc06c_other_organisation_scan_is_404(client, world):
    scan_b = scan_for(world, "repo_b", "dev_b")
    client.force_login(world["dev_a"])
    assert client.get(reverse("scans:detail", args=[scan_b.pk])).status_code == 404


def test_developer_sees_only_own_scans_within_organisation(client, world):
    other = scan_for(world, "repo_a", "dev_a2")
    client.force_login(world["dev_a"])
    assert client.get(reverse("scans:detail", args=[other.pk])).status_code == 404


def test_tc06d_auditor_reads_organisation_but_cannot_upload(client, world):
    scan = scan_for(world, "repo_a", "dev_a")
    client.force_login(world["auditor_a"])
    assert client.get(reverse("scans:detail", args=[scan.pk])).status_code == 200
    assert client.get(reverse("scans:upload")).status_code == 403
    assert client.post(reverse("scans:upload"), {"repository": world["repo_a"].pk}).status_code == 403


def test_auditor_cannot_register_repository_or_change_status(client, world):
    scan = scan_for(world, "repo_a", "dev_a")
    client.force_login(world["auditor_a"])
    assert client.get(reverse("repos:create")).status_code == 403
    assert client.post(reverse("scans:finding_status", args=[scan.pk, 1]), {"status": "fixed"}).status_code == 403


def test_tc06e_admin_can_use_admin_site(client, world):
    client.force_login(world["admin_a"])
    assert client.get("/admin/").status_code == 200


def test_admin_cannot_upload(client, world):
    client.force_login(world["admin_a"])
    assert client.get(reverse("scans:upload")).status_code == 403


def test_dashboard_for_other_organisation_repo_is_404(client, world):
    client.force_login(world["dev_a"])
    assert client.get(f"/dashboard/?repo={world['repo_b'].pk}").status_code == 404
    assert client.get(f"/dashboard/charts/severity.png?repo={world['repo_b'].pk}").status_code == 404


def test_post_without_csrf_token_is_refused(world):
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(world["dev_a"])
    assert strict.post(reverse("scans:upload"), {"repository": world["repo_a"].pk}).status_code == 403
