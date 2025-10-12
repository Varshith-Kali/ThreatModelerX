import subprocess
import json
import uuid
import logging
from typing import List, Dict, Any
from pathlib import Path
from ..models import Finding, SeverityLevel, FindingStatus

class RetireRunner:
    def __init__(self):
        self.tool_name = "retire.js"
        self.logger = logging.getLogger("autothreatmap")

    def run(self, repo_path: str) -> List[Finding]:
        findings = []

        try:
            # Check if retire is installed
            try:
                subprocess.run(["retire", "--version"], capture_output=True, check=False)
            except FileNotFoundError:
                self.logger.warning("Retire.js not found. Using mock data for demonstration.")
                return self._generate_mock_findings(repo_path)
                
            result = subprocess.run(
                ["retire", "--path", repo_path, "--outputformat", "json", "--outputpath", "-"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.stdout:
                data = json.loads(result.stdout)
                findings = self._parse_results(data, repo_path)
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Retire.js scan timed out for {repo_path}")
        except Exception as e:
            self.logger.error(f"Error running retire.js: {e}")

        return findings
        
    def _generate_mock_findings(self, repo_path: str) -> List[Finding]:
        """Generate mock findings for demonstration when retire.js is not available"""
        self.logger.info("Generating mock retire.js findings for demonstration")
        findings = []
        
        # Create a few sample findings
        findings.append(Finding(
            id=f"RETIRE-MOCK-1",
            tool=self.tool_name,
            file_path=str(Path(repo_path) / "node_modules/jquery/dist/jquery.js"),
            line_number=1,
            description="jQuery 1.8.1 vulnerable to XSS attacks",
            severity=SeverityLevel.HIGH,
            rule_id="retire-js-jquery-1.8.1",
            status=FindingStatus.OPEN,
            cwe="CWE-79",
            fix_recommendation="Update jQuery to version 3.5.0 or later"
        ))
        
        findings.append(Finding(
            id=f"RETIRE-MOCK-2",
            tool=self.tool_name,
            file_path=str(Path(repo_path) / "node_modules/lodash/lodash.js"),
            line_number=1,
            description="Prototype pollution in lodash before 4.17.12",
            severity=SeverityLevel.MEDIUM,
            rule_id="retire-js-lodash-4.17.11",
            status=FindingStatus.OPEN,
            cwe="CWE-1321",
            fix_recommendation="Update lodash to version 4.17.12 or later"
        ))
        
        return findings

    def _parse_results(self, data: List[Dict[str, Any]], repo_path: str) -> List[Finding]:
        findings = []

        for file_result in data:
            file_path = file_result.get("file", "unknown")

            for result in file_result.get("results", []):
                for vulnerability in result.get("vulnerabilities", []):
                    severity = self._map_severity(vulnerability.get("severity", "low"))

                    identifiers = vulnerability.get("identifiers", {})
                    cwe = identifiers.get("CWE", [None])[0]
                    if cwe:
                        cwe = f"CWE-{cwe}"

                    finding = Finding(
                        id=f"RETIRE-{uuid.uuid4().hex[:8]}",
                        tool=self.tool_name,
                        language="javascript",
                        file=str(Path(file_path).relative_to(repo_path)) if repo_path in file_path else file_path,
                        line=None,
                        cwe=cwe,
                        severity=severity,
                        description=f"Vulnerable dependency: {result.get('component', 'unknown')} {result.get('version', '')} - {vulnerability.get('info', [''])[0]}",
                        evidence=f"Component: {result.get('component')} Version: {result.get('version')}",
                        fix_suggestion=f"Update to a secure version. See: {vulnerability.get('info', [''])[0] if vulnerability.get('info') else 'documentation'}",
                        status=FindingStatus.OPEN
                    )
                    findings.append(finding)

        return findings

    def _map_severity(self, retire_severity: str) -> SeverityLevel:
        mapping = {
            "critical": SeverityLevel.CRITICAL,
            "high": SeverityLevel.HIGH,
            "medium": SeverityLevel.MEDIUM,
            "low": SeverityLevel.LOW
        }
        return mapping.get(retire_severity.lower(), SeverityLevel.LOW)
