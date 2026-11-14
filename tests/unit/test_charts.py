"""TC-05: chart generation. Reads the data held in the figures, never pixels."""
import charts.render as render

SEVERITY = {"Critical": 2, "High": 3, "Medium": 1, "Low": 0}
PILLARS = {"VCS": 2, "CI/CD": 3, "Registry": 1, "Endpoint / IDE": 0, "Production": 0}


def heights(fig):
    return [p.get_height() for p in fig.axes[0].patches]


def test_tc05a_severity_chart_has_four_bars_including_zero():
    fig = render.severity_figure(SEVERITY)
    assert heights(fig) == [2, 3, 1, 0]
    assert [t.get_text() for t in fig.axes[0].get_xticklabels()] == ["Critical", "High", "Medium", "Low"]


def test_tc05a_severity_order_is_fixed_whatever_the_input_order():
    fig = render.severity_figure({"Low": 0, "Medium": 1, "High": 3, "Critical": 2})
    assert heights(fig) == [2, 3, 1, 0]


def test_tc05b_pillar_chart_has_five_bars_and_same_total():
    fig = render.pillar_figure(PILLARS)
    assert heights(fig) == [2, 3, 1, 0, 0]
    assert sum(heights(fig)) == sum(heights(render.severity_figure(SEVERITY)))


def test_tc05c_empty_and_zero_scans_do_not_raise():
    zero = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    assert heights(render.severity_figure(zero)) == [0, 0, 0, 0]
    assert render.severity_chart({}).startswith(b"\x89PNG")
    assert render.trend_chart([]).startswith(b"\x89PNG")


def test_tc05d_trend_has_points_in_date_order():
    points = [{"date": "2026-11-02", "score": 40}, {"date": "2026-11-05", "score": 25}, {"date": "2026-11-08", "score": 10}]
    ax = render.trend_figure(points).axes[0]
    assert list(ax.lines[0].get_ydata()) == [40, 25, 10]
    assert [t.get_text() for t in ax.get_xticklabels()] == ["2026-11-02", "2026-11-05", "2026-11-08"]


def test_top_rules_chart_widths():
    ax = render.top_rules_figure([["VCS-001", 3], ["CICD-001", 1]]).axes[0]
    assert sorted(p.get_width() for p in ax.patches) == [1, 3]
