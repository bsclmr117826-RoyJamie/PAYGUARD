"""SITF mapper: links every rule to an SITF pillar and technique.

TODO(team): the technique names below are descriptive placeholders. Replace them with
the official technique names/IDs from the SITF case study before the final report.
"""

PILLARS = ["Endpoint / IDE", "VCS", "CI/CD", "Registry", "Production"]

SITF_MAP = {
    # rule code: (pillar, technique)
    "EP-001":   ("Endpoint / IDE", "Sensitive local config committed or exposed"),
    "VCS-001":  ("VCS", "Hardcoded credentials in source repository"),
    "VCS-002":  ("VCS", "Hardcoded credentials in source repository"),
    "VCS-003":  ("VCS", "Hardcoded credentials in source repository"),
    "CICD-001": ("CI/CD", "Unpinned third-party action (imposter commit / pipeline hijack)"),
    "CICD-002": ("CI/CD", "Untrusted code run with privileged workflow trigger"),
    "CICD-003": ("CI/CD", "Over-privileged pipeline token"),
    "REG-001":  ("Registry", "Unpinned dependency (dependency substitution)"),
    "PROD-001": ("Production", "Debug mode enabled in deployed configuration"),
    "PROD-002": ("Production", "Insecure transport (HTTP) for service endpoint"),
}


def map_rule(rule_code: str) -> tuple[str, str]:
    """Return (pillar, technique) for a rule code."""
    return SITF_MAP[rule_code]
