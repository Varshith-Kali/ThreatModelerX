import subprocess
import json
import uuid
import logging
from typing import List, Dict, Any
from pathlib import Path
from ..models import Finding, SeverityLevel, FindingStatus

class SemgrepRunner:
    def __init__(self):
        self.tool_name = "semgrep"
        self.logger = logging.getLogger("autothreatmap")

    def run(self, repo_path: str) -> List[Finding]:
        findings = []

        try:
            # Check if semgrep is installed
            try:
                subprocess.run(["semgrep", "--version"], capture_output=True, check=False)
            except FileNotFoundError:
                self.logger.warning("Semgrep not found. Using mock data for demonstration.")
                return self._generate_mock_findings(repo_path)
                
            result = subprocess.run(
                ["semgrep", "--config=auto", "--json", "--quiet", repo_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode in [0, 1]:
                data = json.loads(result.stdout)
                findings = self._parse_results(data, repo_path)
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Semgrep scan timed out for {repo_path}")
        except Exception as e:
            self.logger.error(f"Error running semgrep: {e}")

        return findings
        
    def _generate_mock_findings(self, repo_path: str) -> List[Finding]:
        """Generate mock findings for demonstration when semgrep is not available"""
        self.logger.info("Generating mock semgrep findings for demonstration")
        findings = []
        
        # Create a few sample findings
        findings.append(Finding(
            id=f"SEMGREP-MOCK-1",
            tool=self.tool_name,
            file_path=str(Path(repo_path) / "app.js"),
            line_number=42,
            description="Potential XSS vulnerability in user input handling",
            severity=SeverityLevel.HIGH,
            rule_id="javascript.express.security.audit.xss.xss-unsafe-variable",
            status=FindingStatus.OPEN,
            cwe="CWE-79",
            fix_recommendation="Sanitize user input before rendering to prevent XSS attacks"
        ))
        
        findings.append(Finding(
            id=f"SEMGREP-MOCK-2",
            tool=self.tool_name,
            file_path=str(Path(repo_path) / "routes/users.js"),
            line_number=23,
            description="SQL Injection vulnerability in query construction",
            severity=SeverityLevel.CRITICAL,
            rule_id="javascript.express.security.audit.sql-injection.sql-injection",
            status=FindingStatus.OPEN,
            cwe="CWE-89",
            fix_recommendation="Use parameterized queries or an ORM to prevent SQL injection"
        ))
        
        return findings

    def _parse_results(self, data: Dict[str, Any], repo_path: str) -> List[Finding]:
        findings = []

        for result in data.get("results", []):
            severity = self._map_severity(result.get("extra", {}).get("severity", "INFO"))

            cwe = None
            metadata = result.get("extra", {}).get("metadata", {})
            if "cwe" in metadata:
                cwe_list = metadata["cwe"]
                if isinstance(cwe_list, list) and len(cwe_list) > 0:
                    cwe = f"CWE-{cwe_list[0]}"

            finding = Finding(
                id=f"SEMGREP-{uuid.uuid4().hex[:8]}",
                tool=self.tool_name,
                language=result.get("extra", {}).get("metadata", {}).get("technology", ["unknown"])[0],
                file=str(Path(result["path"]).relative_to(repo_path)) if repo_path in result["path"] else result["path"],
                line=result.get("start", {}).get("line"),
                cwe=cwe,
                severity=severity,
                description=result.get("extra", {}).get("message", "Security issue detected"),
                evidence=result.get("extra", {}).get("lines", ""),
                fix_suggestion=metadata.get("fix", "Review and fix the security issue"),
                status=FindingStatus.OPEN
            )
            findings.append(finding)

        return findings

    def _map_severity(self, semgrep_severity: str) -> SeverityLevel:
        mapping = {
            "ERROR": SeverityLevel.HIGH,
            "WARNING": SeverityLevel.MEDIUM,
            "INFO": SeverityLevel.LOW
        }
        return mapping.get(semgrep_severity.upper(), SeverityLevel.LOW)
