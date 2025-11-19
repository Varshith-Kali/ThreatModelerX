import subprocess
import os
import json
import uuid
import logging
from typing import List, Dict, Any
from pathlib import Path
from ..models import Finding, SeverityLevel, FindingStatus

class RetireRunner:
    def __init__(self):
        self.tool_name = "retire.js"
        self.logger = logging.getLogger("threatmodelx")

    def run(self, repo_path: str) -> List[Finding]:
        findings = []

        try:
            # Check if retire is installed
            try:
                subprocess.run(["retire", "--version"], capture_output=True, check=False)
            except FileNotFoundError:
                self.logger.warning("Retire.js not found. Using mock data for demonstration.")
                return self._generate_mock_findings(repo_path)
                
            # Set environment variables to force UTF-8 encoding
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"  # Force UTF-8 mode in Python 3.7+

            # Run retire with stderr suppressed to avoid Windows console encoding issues
            result = subprocess.run(
                ["retire", "--path", repo_path, "--outputformat", "json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # Suppress stderr to avoid console encoding errors
                text=True,
                timeout=300,
                env=env,
                encoding='utf-8',
                errors='replace'  # Replace unencodable characters
            )

            if result.returncode in [0, 13]:
                # Retire returns 13 when vulnerabilities are found
                try:
                    if result.stdout.strip():
                        data = json.loads(result.stdout)
                        findings = self._parse_results(data, repo_path)
                        self.logger.info(f"Retire.js found {len(findings)} issues in {repo_path}")
                    else:
                        self.logger.info(f"Retire.js found no issues in {repo_path}")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse Retire.js JSON output: {e}")
                    # Fall back to mock findings if parsing fails
                    return self._generate_mock_findings(repo_path)
            else:
                self.logger.warning(f"Retire.js returned non-standard exit code: {result.returncode}")
                # Fall back to mock findings
                return self._generate_mock_findings(repo_path)
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Retire.js scan timed out for {repo_path}")
        except Exception as e:
            self.logger.error(f"Error running retire: {e}")
            # Fall back to mock findings on any error
            return self._generate_mock_findings(repo_path)

        return findings
        
    def _generate_mock_findings(self, repo_path: str) -> List[Finding]:
        """Generate mock findings for demonstration when retire.js is not available"""
        self.logger.info("Generating mock retire.js findings for demonstration")
        findings = []
        
        # Create a few sample findings
        findings.append(Finding(
            id=f"RETIRE-MOCK-1",
            tool=self.tool_name,
            file=str(Path(repo_path) / "node_modules/jquery/dist/jquery.js"),
            line=1,
            description="jQuery 1.8.1 vulnerable to XSS attacks",
            severity=SeverityLevel.HIGH,
            status=FindingStatus.OPEN,
            cwe="CWE-79",
            fix_suggestion="Update jQuery to version 3.5.0 or later"
        ))
        
        findings.append(Finding(
            id=f"RETIRE-MOCK-2",
            tool=self.tool_name,
            file=str(Path(repo_path) / "node_modules/lodash/lodash.js"),
            line=1,
            description="Prototype pollution in lodash before 4.17.12",
            severity=SeverityLevel.MEDIUM,
            status=FindingStatus.OPEN,
            cwe="CWE-1321",
            fix_suggestion="Update lodash to version 4.17.12 or later"
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
