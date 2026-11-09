# payguard_backend/domain/rule_engine.py
import re

class PayGuardRuleEngine:
    """
    Core rule engine that scans code/YAML content against defined SITF rules.
    """
    RULES = [
        {
            "code": "RULE-VCS-01",
            "pillar": "VCS",
            "severity": "CRITICAL",
            "weight": 10,
            "pattern": r'(consumer_secret|daraja_secret|passkey|shortcode_key)\s*=\s*["\'][A-Za-z0-9_-]{8,}["\']',
            "description": "Hardcoded Daraja Consumer Key / Secret in Source Code"
        },
        {
            "code": "RULE-CICD-01",
            "pillar": "CI/CD",
            "severity": "HIGH",
            "weight": 5,
            "pattern": r'uses:\s*actions/[a-zA-Z0-9_-]+@(main|master|v[0-9]+)',
            "description": "Unpinned GitHub Action Runner (Missing Commit SHA)"
        },
        {
            "code": "RULE-PROD-01",
            "pillar": "Production",
            "severity": "HIGH",
            "weight": 5,
            "pattern": r'def\s+mpesa_callback\(request\):(?![\s\S]*validate_signature)',
            "description": "Unvalidated M-Pesa Payment Callback Endpoint"
        },
        {
            "code": "RULE-PROD-02",
            "pillar": "Production",
            "severity": "HIGH",
            "weight": 5,
            "pattern": r'DEBUG\s*=\s*True',
            "description": "DEBUG=True Enabled in Django Settings"
        },
        {
            "code": "RULE-IDE-01",
            "pillar": "Endpoint/IDE",
            "severity": "MEDIUM",
            "weight": 2,
            "pattern": r'^(?!.*\.env).*$',
            "description": "Missing .env exclusion in .gitignore configuration"
        }
    ]

    @classmethod
    def scan_content(cls, file_path, content):
        findings = []
        lines = content.splitlines()
        for rule in cls.RULES:
            pattern = re.compile(rule["pattern"], re.MULTILINE)
            for idx, line in enumerate(lines, start=1):
                if pattern.search(line):
                    # Secret masking logic: store first 4 characters max
                    masked = line.strip()[:15] + "...[MASKED_BY_PAYGUARD]"
                    findings.append({
                        "rule_code": rule["code"],
                        "pillar": rule["pillar"],
                        "description": rule["description"],
                        "severity": rule["severity"],
                        "weight": rule["weight"],
                        "file_path": file_path,
                        "line_number": idx,
                        "masked_evidence": masked
                    })
        return findings