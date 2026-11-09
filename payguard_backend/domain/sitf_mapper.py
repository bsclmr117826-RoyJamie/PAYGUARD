# payguard_backend/domain/sitf_mapper.py

class SITFMapper:
    """
    Maps detected scan rules to SITF (SDLC Infrastructure Threat Framework) pillars & techniques.
    """
    SITF_MAPPING = {
        "RULE-VCS-01": {"pillar": "VCS", "technique": "SITF-T1012: Stolen API Secrets"},
        "RULE-CICD-01": {"pillar": "CI/CD", "technique": "SITF-T1045: Unpinned Pipeline Actions"},
        "RULE-PROD-01": {"pillar": "Production", "technique": "SITF-T1078: Unauthenticated Callback"},
        "RULE-PROD-02": {"pillar": "Production", "technique": "SITF-T1080: Debug Mode Key Leak"},
        "RULE-IDE-01": {"pillar": "Endpoint/IDE", "technique": "SITF-T1001: Developer Env Exposure"}
    }

    @classmethod
    def get_technique(cls, rule_code):
        return cls.SITF_MAPPING.get(rule_code, {"pillar": "General", "technique": "SITF-T1000: Generic Vulnerability"})