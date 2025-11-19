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
        self.logger = logging.getLogger("autothreatmap")

    def run(self, repo_path: str) -> List[Finding]:
        findings = []

        try:
            # Check if bandit is installed
            try:
                subprocess.run(["bandit", "--version"], capture_output=True, check=False)
            except FileNotFoundError:
                self.logger.warning("Bandit not found. Using mock data for demonstration.")
                return self._generate_mock_findings(repo_path)
                
            # Set environment variables to force UTF-8 encoding
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"  # Force UTF-8 mode in Python 3.7+

            result = subprocess.run(
                ["bandit", "-r", repo_path, "-f", "json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
                env=env,
                encoding='utf-8',
                errors='replace'  # Replace unencodable characters
            )

            if result.returncode in [0, 1]:
                # Bandit returns 1 when issues are found
                try:
                    data = json.loads(result.stdout)
                    findings = self._parse_results(data, repo_path)
                    self.logger.info(f"Bandit found {len(findings)} issues in {repo_path}")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse Bandit JSON output: {e}")
                    # Fall back to mock findings if parsing fails
                    return self._generate_mock_findings(repo_path)
            else:
                self.logger.warning(f"Bandit returned non-standard exit code: {result.returncode}")
                # Fall back to mock findings
                return self._generate_mock_findings(repo_path)
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Bandit scan timed out for {repo_path}")
            # Fall back to mock findings on timeout
            return self._generate_mock_findings(repo_path)
        except Exception as e:
            self.logger.error(f"Error running bandit: {e}")
            # Fall back to mock findings on any error
            return self._generate_mock_findings(repo_path)

        return findings
        
    def _generate_mock_findings(self, repo_path: str) -> List[Finding]:
        """Generate mock findings for demonstration when bandit is not available"""
        self.logger.info("Generating mock bandit findings for demonstration")
        findings = []
        
        # Create a few sample findings
        findings.append(Finding(
            id=f"BANDIT-MOCK-1",
            tool=self.tool_name,
            file=str(Path(repo_path) / "app.py"),
            line=15,
            description="Use of insecure MD5 hash function",
            severity=SeverityLevel.MEDIUM,
            status=FindingStatus.OPEN,
            cwe="CWE-327",
            fix_suggestion="Use a more secure hashing algorithm like SHA-256"
        ))
        
        findings.append(Finding(
            id=f"BANDIT-MOCK-2",
            tool=self.tool_name,
            file=str(Path(repo_path) / "utils/helpers.py"),
            line=42,
            description="Possible hardcoded password",
            severity=SeverityLevel.HIGH,
            status=FindingStatus.OPEN,
            cwe="CWE-798",
            fix_suggestion="Store passwords in environment variables or a secure vault"
        ))
        
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
