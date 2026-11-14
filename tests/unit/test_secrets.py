from scanner import scan_text


def test_tc01_detects_hardcoded_daraja_secret():
    """TC-01: Critical VCS finding with masked evidence."""
    code = 'consumer_secret = "abc123XYZ789secretKEY"\n'
    findings = scan_text(code, "settings.py")
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_code == "VCS-001"
    assert f.severity == "Critical"
    assert f.pillar == "VCS"
    assert f.line_number == 1
    assert f.masked_evidence.startswith("abc1")
    assert "abc123XYZ789secretKEY" not in f.masked_evidence   # full value never kept


def test_json_style_key_is_detected():
    findings = scan_text('{"consumer_key": "Zx9Kq2Lm8Pw4Rt6Y"}', "config.json")
    assert [f.rule_code for f in findings] == ["VCS-001"]


def test_passkey_is_detected():
    findings = scan_text('PASSKEY = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"', "mpesa.py")
    assert [f.rule_code for f in findings] == ["VCS-002"]
    assert findings[0].severity == "Critical"


def test_github_token_is_detected():
    token = "ghp_" + "A1b2" * 9
    findings = scan_text(f'token = "{token}"', "deploy.py")
    assert [f.rule_code for f in findings] == ["VCS-003"]
    assert token not in findings[0].masked_evidence


def test_django_secret_key_is_detected():
    findings = scan_text('SECRET_KEY = "django-insecure-k3y9v8x7w6u5"', "settings.py")
    assert [f.rule_code for f in findings] == ["VCS-003"]


def test_secret_read_from_environment_is_not_flagged():
    assert scan_text('consumer_secret = os.environ["MPESA_SECRET"]', "settings.py") == []


def test_placeholder_values_are_not_flagged():
    assert scan_text('api_key = "your-api-key-here"', "settings.py") == []


def test_daraja_named_secret_is_detected():
    # Variable names such as daraja_secret / daraja_key (used in the QA defect report, BUG-001).
    for line in ('daraja_secret = "bf918342abcdef123456"', 'DARAJA_KEY: "bf918342abcdef123456"'):
        findings = scan_text(line, "config.py")
        assert [f.rule_code for f in findings] == ["VCS-001"]
        assert findings[0].masked_evidence == "bf91********"
