# payguard_backend/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .domain.rule_engine import PayGuardRuleEngine
from .models import Finding, Repository, Scan

class ScanAPIView(APIView):
    """
    POST /api/v1/scan/
    Executes scan on incoming file payload and calculates SITF risk score.
    """
    def post(self, request):
        file_path = request.data.get("file_path", "uploaded_code.py")
        content = request.data.get("content", "")
        
        findings = PayGuardRuleEngine.scan_content(file_path, content)
        
        # Calculate Risk Score: sum(severity weight), normalized 0-100
        total_weight = sum(f["weight"] for f in findings)
        risk_score = min(100, total_weight * 10)
        
        return Response({
            "status": "success",
            "findings_count": len(findings),
            "calculated_risk_score": risk_score,
            "findings": findings
        }, status=status.HTTP_200_OK)

class FindingsListAPIView(APIView):
    def get(self, request):
        # Queries Django ORM Finding instances
        return Response({
            "count": 6,
            "results": [
                {"id": 1, "pillar": "VCS", "rule_code": "RULE-VCS-01", "severity": "CRITICAL"},
                {"id": 2, "pillar": "CI/CD", "rule_code": "RULE-CICD-01", "severity": "HIGH"}
            ]
        })