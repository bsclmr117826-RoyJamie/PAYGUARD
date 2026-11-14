import json
from pathlib import Path

import pytest

from scanner import scan_text

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
CASES = json.loads((SAMPLES / "expected.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=[c["file"] for c in CASES])
def test_sample_gives_expected_rule_codes(case):
    text = (SAMPLES / case["file"]).read_text()
    codes = sorted(f.rule_code for f in scan_text(text, case["path"]))
    assert codes == sorted(case["codes"])


def test_our_own_workflow_has_no_cicd_findings():
    workflow = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
    findings = [f for f in scan_text(workflow.read_text(), ".github/workflows/ci.yml") if f.pillar == "CI/CD"]
    assert findings == []
