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
            try:
                subprocess.run(["retire", "--version"], capture_output=True, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                self.logger.error("Retire.js is not installed or not found in PATH. Please install retire to use this scanner.")
                self.logger.error("Install with: npm install -g retire")
                return []
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            self.logger.info(f"Running Retire.js scan on {repo_path}")
            result = subprocess.run(
                ["retire", "--path", repo_path, "--outputformat", "json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode in [0, 13]:
                try:
                    if result.stdout.strip():
                        data = json.loads(result.stdout)
                        findings = self._parse_results(data, repo_path)
                        self.logger.info(f"Retire.js found {len(findings)} issues in {repo_path}")
                    else:
                        self.logger.info(f"Retire.js found no issues in {repo_path}")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse Retire.js JSON output: {e}")
                    return []
            else:
                self.logger.error(f"Retire.js scan failed with exit code: {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                return []
        except subprocess.TimeoutExpired:
            self.logger.error(f"Retire.js scan timed out for {repo_path}")
            return []
        except Exception as e:
            self.logger.error(f"Error running retire: {e}")
            return []
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
