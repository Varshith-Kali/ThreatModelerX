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
                subprocess.run(["semgrep", "--version"], capture_output=True, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                self.logger.error("Semgrep is not installed or not found in PATH.")
                self.logger.error("Install with: pip install semgrep")
                return []
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            env["SEMGREP_ENABLE_VERSION_CHECK"] = "0"
            self.logger.info(f"Running ENHANCED Semgrep scan with multiple rulesets on {repo_path}")
            result = subprocess.run(
                [
                    "semgrep",
                    "--config=auto",
                    "--config=p/security-audit",
                    "--config=p/owasp-top-ten",
                    "--config=p/cwe-top-25",
                    "--json",
                    "--quiet",
                    "--no-git-ignore",
                    repo_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=600,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode in [0, 1]:
                try:
                    data = json.loads(result.stdout)
                    findings = self._parse_results(data, repo_path)
                    self.logger.info(f"Semgrep ENHANCED scan found {len(findings)} issues in {repo_path}")
                    self.logger.info(f"Rulesets used: auto, security-audit, owasp-top-ten, cwe-top-25")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse Semgrep JSON output: {e}")
                    return []
            else:
                self.logger.error(f"Semgrep scan failed with exit code: {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                return []
        except subprocess.TimeoutExpired:
            self.logger.error(f"Semgrep scan timed out for {repo_path}")
            return []
        except Exception as e:
            self.logger.error(f"Error running semgrep: {e}")
            return []
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
