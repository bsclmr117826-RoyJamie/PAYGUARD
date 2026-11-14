from scanner import scan_text

WORKFLOW = ".github/workflows/ci.yml"
SHA = "a" * 40


def codes(findings):
    return [f.rule_code for f in findings]


def test_tc02_unpinned_action_is_flagged():
    """TC-02: High CI/CD finding mapped to its SITF pillar."""
    text = "steps:\n  - uses: actions/checkout@main\n"
    findings = scan_text(text, WORKFLOW)
    assert codes(findings) == ["CICD-001"]
    assert findings[0].severity == "High"
    assert findings[0].pillar == "CI/CD"
    assert findings[0].line_number == 2


def test_sha_pinned_action_is_not_flagged():
    assert scan_text(f"steps:\n  - uses: actions/checkout@{SHA}\n", WORKFLOW) == []


def test_local_action_is_not_flagged():
    assert scan_text("steps:\n  - uses: ./local-action\n", WORKFLOW) == []


def test_tc03_clean_workflow_has_zero_findings():
    """TC-03: a clean workflow passes."""
    clean = f"""name: CI
on: [push]
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@{SHA}
      - run: pytest
"""
    assert scan_text(clean, WORKFLOW) == []


def test_pull_request_target_with_untrusted_checkout_is_flagged():
    text = f"""on: pull_request_target
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@{SHA}
        with:
          ref: ${{{{ github.event.pull_request.head.sha }}}}
"""
    assert codes(scan_text(text, WORKFLOW)) == ["CICD-002"]


def test_pull_request_target_without_untrusted_code_is_not_flagged():
    text = f"on: pull_request_target\njobs:\n  x:\n    steps:\n      - uses: actions/checkout@{SHA}\n"
    assert scan_text(text, WORKFLOW) == []


def test_write_all_permissions_is_flagged():
    findings = scan_text("on: push\npermissions: write-all\n", WORKFLOW)
    assert codes(findings) == ["CICD-003"]


def test_workflow_rules_ignore_other_files():
    assert scan_text("uses: actions/checkout@main", "notes.txt") == []


def test_malformed_yaml_does_not_crash():
    assert scan_text("on: [unclosed\n  - : :", WORKFLOW) == []
