from scanner import scan_text


def codes(findings):
    return [f.rule_code for f in findings]


def test_unpinned_dependencies_are_flagged():
    text = "django>=5.0\nrequests\nflask==3.0.0\n# a comment\n-r base.txt\n"
    findings = scan_text(text, "requirements.txt")
    assert codes(findings) == ["REG-001", "REG-001"]
    assert [f.line_number for f in findings] == [1, 2]
    assert findings[0].pillar == "Registry"


def test_fully_pinned_requirements_pass():
    assert scan_text("django==5.0.1\npytest-django==4.8.0  # tests\n", "requirements.txt") == []


def test_debug_true_is_flagged():
    findings = scan_text("DEBUG = True\n", "settings.py")
    assert codes(findings) == ["PROD-001"]
    assert findings[0].pillar == "Production"


def test_debug_false_or_env_driven_is_not_flagged():
    assert scan_text("DEBUG = False\n", "settings.py") == []
    assert scan_text('DEBUG = os.environ.get("DEBUG") == "1"\n', "settings.py") == []


def test_http_callback_is_flagged_and_query_string_dropped():
    text = 'CALLBACK_URL = "http://pay.example-shop.co.ke/callback?token=abc"\n'
    findings = scan_text(text, "settings.py")
    assert codes(findings) == ["PROD-002"]
    assert "token" not in findings[0].masked_evidence


def test_https_and_localhost_are_not_flagged():
    assert scan_text('CALLBACK_URL = "https://pay.example-shop.co.ke/cb"\n', "settings.py") == []
    assert scan_text('API_URL = "http://localhost:8000/api"\n', "settings.py") == []
