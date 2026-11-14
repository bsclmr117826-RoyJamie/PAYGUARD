from django.http import Http404, HttpResponse
from django.shortcuts import render

import charts.render as chart_render
from accounts.permissions import ADMIN, AUDITOR, DEVELOPER, role_required
from repos.selectors import repositories_for_user

from .services import build_dashboard_data

CHARTS = {
    "severity": lambda d: chart_render.severity_chart(d["severity_counts"]),
    "pillar": lambda d: chart_render.pillar_chart(d["pillar_counts"]),
    "trend": lambda d: chart_render.trend_chart(d["trend"]),
    "rules": lambda d: chart_render.top_rules_chart(d["top_rules"]),
}


def _repo_id(request):
    raw = request.GET.get("repo", "")
    return int(raw) if raw.isdigit() else None


@role_required(DEVELOPER, AUDITOR, ADMIN)
def home(request):
    data = build_dashboard_data(request.user, _repo_id(request))
    return render(request, "dashboard/home.html", {
        "data": data,
        "repositories": repositories_for_user(request.user),
        "selected_repo_id": data["repository"]["id"] if data["repository"] else None,
    })


@role_required(DEVELOPER, AUDITOR, ADMIN)
def chart(request, kind):
    if kind not in CHARTS:
        raise Http404
    png = CHARTS[kind](build_dashboard_data(request.user, _repo_id(request)))
    response = HttpResponse(png, content_type="image/png")
    response["Cache-Control"] = "no-store"
    return response
