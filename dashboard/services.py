from django.utils import timezone

from repos.selectors import get_repository_for_user
from scanner import count_by_pillar, count_by_severity, top_rules
from scans.models import Scan
from scans.selectors import scans_for_user


def build_dashboard_data(user, repo_id=None) -> dict:
    """Plain dictionary for the dashboard page and the charts (section 5.3 of the design)."""
    scans = scans_for_user(user).filter(status=Scan.Status.COMPLETE)
    if repo_id is not None:
        repository = get_repository_for_user(user, repo_id)       # 404 if outside the user's scope
    else:
        newest = scans.first()
        repository = newest.repository if newest else None

    latest, findings, trend = None, [], []
    if repository is not None:
        repo_scans = scans.filter(repository=repository)
        latest = repo_scans.first()
        if latest is not None:
            findings = list(latest.findings.all())
        recent = list(repo_scans[:10])[::-1]                      # oldest first
        trend = [{"date": timezone.localtime(s.started_at).date().isoformat(), "score": s.risk_score} for s in recent]

    return {
        "repository": {"id": repository.pk, "name": repository.name} if repository else None,
        "latest_scan": {
            "id": latest.pk,
            "risk_score": latest.risk_score,
            "total_findings": latest.total_findings,
            "started_at": timezone.localtime(latest.started_at).date().isoformat(),
        } if latest else None,
        "severity_counts": count_by_severity(findings),
        "pillar_counts": count_by_pillar(findings),
        "trend": trend,
        "top_rules": [[code, n] for code, n in top_rules(findings, 5)],
    }
