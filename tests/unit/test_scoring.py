from scanner import Finding, calculate_risk_score, count_by_pillar, count_by_severity, top_rules


def make(severity, code="X-1", pillar="VCS"):
    return Finding(code, "t", severity, pillar, "tech", "f.py", 1, "ev")


def test_score_uses_severity_weights():
    findings = [make("Critical"), make("High"), make("High"), make("Medium"), make("Low")]
    assert calculate_risk_score(findings) == 10 + 5 + 5 + 2 + 1


def test_score_is_capped_at_100():
    assert calculate_risk_score([make("Critical")] * 11) == 100


def test_no_findings_scores_zero():
    assert calculate_risk_score([]) == 0


def test_counts_include_zero_buckets():
    findings = [make("Critical"), make("High", pillar="CI/CD")]
    assert count_by_severity(findings) == {"Critical": 1, "High": 1, "Medium": 0, "Low": 0}
    pillars = count_by_pillar(findings)
    assert pillars["VCS"] == 1 and pillars["CI/CD"] == 1 and pillars["Registry"] == 0


def test_top_rules_orders_by_frequency():
    findings = [make("High", "A"), make("High", "B"), make("High", "B")]
    assert top_rules(findings, 5) == [("B", 2), ("A", 1)]
