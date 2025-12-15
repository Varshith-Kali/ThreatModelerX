import subprocess
import os
import json
import uuid
import logging
from typing import List, Dict, Any
from pathlib import Path
from ..models import Finding, SeverityLevel, FindingStatus

class BanditRunner:
    def __init__(self):
        self.tool_name = "bandit"
        self.logger = logging.getLogger("threatmodelx")

    def run(self, repo_path: str) -> List[Finding]:
        findings = []

        try:
            # Check if bandit is installed
            try:
                subprocess.run(["bandit", "--version"], capture_output=True, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                self.logger.error("Bandit is not installed or not found in PATH. Please install bandit to use this scanner.")
                self.logger.error("Install with: pip install bandit")
                return []
                
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"  # Force UTF-8 mode in Python 3.7+

            self.logger.info(f"Running Bandit scan on {repo_path}")
            result = subprocess.run(
                ["bandit", "-r", repo_path, "-f", "json", "--recursive"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
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
                    self.logger.info(f"Bandit found {len(findings)} issues in {repo_path}")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse Bandit JSON output: {e}")
                    return []
            else:
                self.logger.error(f"Bandit scan failed with exit code: {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Bandit scan timed out for {repo_path}")
            return []
        except Exception as e:
            self.logger.error(f"Error running bandit: {e}")
            return []

        return findings

    def _parse_results(self, data: Dict[str, Any], repo_path: str) -> List[Finding]:
        findings = []

        for result in data.get("results", []):
            severity = self._map_severity(
                result.get("issue_severity", "LOW"),
                result.get("issue_confidence", "LOW")
            )

            cwe_id = result.get("issue_cwe", {}).get("id")
            cwe = f"CWE-{cwe_id}" if cwe_id else None

            finding = Finding(
                id=f"BANDIT-{uuid.uuid4().hex[:8]}",
                tool=self.tool_name,
                language="python",
                file=str(Path(result["filename"]).relative_to(repo_path)) if repo_path in result["filename"] else result["filename"],
                line=result.get("line_number"),
                cwe=cwe,
                severity=severity,
                description=f"{result.get('issue_text', 'Security issue')} (Test: {result.get('test_name', 'unknown')})",
                evidence=result.get("code", ""),
                fix_suggestion=result.get("more_info", "Review the security issue and apply appropriate fixes"),
                status=FindingStatus.OPEN
            )
            findings.append(finding)

        return findings

    def _map_severity(self, severity: str, confidence: str) -> SeverityLevel:
        if severity == "HIGH" and confidence in ["HIGH", "MEDIUM"]:
            return SeverityLevel.HIGH
        elif severity == "HIGH" and confidence == "LOW":
            return SeverityLevel.MEDIUM
        elif severity == "MEDIUM":
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
