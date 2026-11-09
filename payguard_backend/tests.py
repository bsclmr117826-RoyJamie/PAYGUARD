# payguard_backend/tests/test_rules.py
import pytest
from payguard_backend.domain.rule_engine import PayGuardRuleEngine

def test_detect_daraja_secret():
    code = 'daraja_secret = "bf918342abcdef123456"'
    findings = PayGuardRuleEngine.scan_content('config.py', code)
    assert len(findings) == 1
    assert findings[0]["rule_code"] == "RULE-VCS-01"
    assert findings[0]["severity"] == "CRITICAL"

def test_clean_code_passes():
    code = 'def calculate_tax(amount):
    return amount * 0.16'
    findings = PayGuardRuleEngine.scan_content('math.py', code)
    assert len(findings) == 0