"""Risk score and counting helpers (the dashboard developer can call these directly)."""
from collections import Counter

from scanner.sitf import PILLARS

SEVERITY_WEIGHTS = {"Critical": 10, "High": 5, "Medium": 2, "Low": 1}
MAX_SCORE = 100


def calculate_risk_score(findings) -> int:
    """sum(severity weight x count), capped at 100.

    DECISION TO CONFIRM: the proposal says 'normalised to 0-100' without a method.
    Capping at 100 is the simplest option. Change this function if the team agrees
    on something else (e.g. dividing by the number of files scanned).
    """
    raw = sum(SEVERITY_WEIGHTS.get(f.severity, 0) for f in findings)
    return min(MAX_SCORE, raw)


def count_by_severity(findings) -> dict:
    counts = Counter(f.severity for f in findings)
    return {sev: counts.get(sev, 0) for sev in SEVERITY_WEIGHTS}


def count_by_pillar(findings) -> dict:
    counts = Counter(f.pillar for f in findings)
    return {pillar: counts.get(pillar, 0) for pillar in PILLARS}


def top_rules(findings, n: int = 5) -> list[tuple[str, int]]:
    """The n most frequently triggered rules, for the 'Top 5 rules' chart."""
    return Counter(f.rule_code for f in findings).most_common(n)
