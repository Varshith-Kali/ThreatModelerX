from typing import List
from ..models import Finding, SeverityLevel

class RiskScorer:
    SEVERITY_WEIGHTS = {
        SeverityLevel.CRITICAL: 10.0,
        SeverityLevel.HIGH: 6.0,
        SeverityLevel.MEDIUM: 3.0,
        SeverityLevel.LOW: 1.0
    }

    EXPLOITABILITY = {
        "CWE-89": 0.9,
        "CWE-78": 0.9,
        "CWE-79": 0.8,
        "CWE-502": 0.85,
        "CWE-798": 0.95,
        "CWE-95": 0.9,
        "CWE-338": 0.5,
        "CWE-942": 0.7,
        "CWE-489": 0.6,
        "CWE-250": 0.7
    }

    def calculate_risk(self, finding: Finding) -> float:
        severity_weight = self.SEVERITY_WEIGHTS.get(finding.severity, 1.0)

        exploitability = 0.5
        if finding.cwe:
            exploitability = self.EXPLOITABILITY.get(finding.cwe, 0.5)

        asset_value = 3.0
        if any(keyword in finding.file.lower() for keyword in ["auth", "login", "admin", "payment"]):
            asset_value = 5.0
        elif any(keyword in finding.file.lower() for keyword in ["api", "endpoint", "route"]):
            asset_value = 4.0

        exposure_factor = 1.0
        if any(keyword in finding.description.lower() for keyword in ["remote", "unauthenticated", "public"]):
            exposure_factor = 1.5

        risk_score = severity_weight * exploitability * asset_value * exposure_factor

        return round(risk_score, 2)

    def calculate_overall_risk(self, findings: List[Finding]) -> float:
        if not findings:
            return 0.0

        critical_count = len([f for f in findings if f.severity == SeverityLevel.CRITICAL])
        high_count = len([f for f in findings if f.severity == SeverityLevel.HIGH])
        medium_count = len([f for f in findings if f.severity == SeverityLevel.MEDIUM])
        low_count = len([f for f in findings if f.severity == SeverityLevel.LOW])

        weighted_score = (
            critical_count * 10.0 +
            high_count * 6.0 +
            medium_count * 3.0 +
            low_count * 1.0
        )

        total_findings = len(findings)
        normalized_score = min((weighted_score / max(total_findings, 1)) * 10, 100.0)

        return round(normalized_score, 2)
