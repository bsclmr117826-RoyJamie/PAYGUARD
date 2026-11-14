"""BUG-001 from the QA defect report: the old rule RULE-IDE-01 fired on ordinary source lines.

The scanner evaluates EP-001 (.env not in .gitignore) once per project folder, never per source line.
"""
from scanner import scan_text


def test_bug001_daraja_secret_gives_exactly_one_critical_finding():
    findings = scan_text('daraja_secret = "bf918342abcdef123456"', "config.py")
    assert [(f.rule_code, f.severity) for f in findings] == [("VCS-001", "Critical")]


def test_bug001_clean_code_gives_zero_findings():
    assert scan_text("def calculate_tax(amount):\n    return amount * 0.16", "math.py") == []


def test_bug001_masking_keeps_only_four_characters_of_the_secret():
    (finding,) = scan_text('passkey = "Abcd1234efgh5678"', "config.py")
    assert "Abcd1" not in finding.masked_evidence and "efgh" not in finding.masked_evidence
