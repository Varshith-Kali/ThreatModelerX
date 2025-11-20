import subprocess
import os
import json
import uuid
import logging
from typing import List, Dict, Any
from pathlib import Path
from ..models import Finding, SeverityLevel, FindingStatus

class SemgrepRunner:
    def __init__(self):
        self.tool_name = "semgrep"
        self.logger = logging.getLogger("threatmodelx")

    def run(self, repo_path: str) -> List[Finding]:
        findings = []

        try:
            try:
                subprocess.run(["semgrep", "--version"], capture_output=True, check=False)
            except FileNotFoundError:
                self.logger.warning("Semgrep not found. Using mock data for demonstration.")
                return self._generate_mock_findings(repo_path)
                
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"  # Force UTF-8 mode in Python 3.7+

            result = subprocess.run(
                ["semgrep", "--config=auto", "--json", "--quiet", repo_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=300,
                env=env,
                encoding='utf-8',
                errors='replace'  # Replace unencodable characters
            )

            if result.returncode in [0, 1]:
                try:
                    data = json.loads(result.stdout)
                    findings = self._parse_results(data, repo_path)
                    self.logger.info(f"Semgrep found {len(findings)} issues in {repo_path}")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse Semgrep JSON output: {e}")
                    return self._generate_mock_findings(repo_path)
            else:
                self.logger.warning(f"Semgrep returned non-standard exit code: {result.returncode}")
                return self._generate_mock_findings(repo_path)
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Semgrep scan timed out for {repo_path}")
        except Exception as e:
            self.logger.error(f"Error running semgrep: {e}")
            return self._generate_mock_findings(repo_path)

        return findings
        
    def _generate_mock_findings(self, repo_path: str) -> List[Finding]:
        """Generate mock findings for demonstration when semgrep is not available"""
        self.logger.info("Generating mock semgrep findings for demonstration")
        findings = []
        
        # Create a few sample findings
        findings.append(Finding(
            id=f"SEMGREP-MOCK-1",
            tool=self.tool_name,
            file=str(Path(repo_path) / "app.js"),
            line=42,
            description="Potential XSS vulnerability in user input handling",
            severity=SeverityLevel.HIGH,
            status=FindingStatus.OPEN,
            cwe="CWE-79",
            fix_suggestion="Sanitize user input before rendering to prevent XSS attacks"
        ))
        
        findings.append(Finding(
            id=f"SEMGREP-MOCK-2",
            tool=self.tool_name,
            file=str(Path(repo_path) / "routes/users.js"),
            line=23,
            description="SQL Injection vulnerability in query construction",
            severity=SeverityLevel.CRITICAL,
            status=FindingStatus.OPEN,
            cwe="CWE-89",
            fix_suggestion="Use parameterized queries or an ORM to prevent SQL injection"
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
