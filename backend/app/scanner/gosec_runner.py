import logging
import subprocess
import json
import os
import tempfile
from typing import List, Dict, Any, Optional

from ..models import Finding, SeverityLevel, ScanRequest

logger = logging.getLogger("autothreatmap.scanner.gosec")

class GosecRunner:
    """
    Gosec scanner for Go code analysis
    """
    
    def __init__(self, gosec_path: Optional[str] = None):
        """
        Initialize the Gosec scanner
        
        Args:
            gosec_path: Path to gosec binary (optional)
        """
        self.gosec_path = gosec_path or "gosec"
        
    async def scan(self, scan_request: ScanRequest) -> List[Finding]:
        """
        Run Gosec scan on Go code
        
        Args:
            scan_request: The scan request containing repo path
            
        Returns:
            List of security findings
        """
        repo_path = scan_request.repo_path
        logger.info(f"Starting Gosec scan on {repo_path}")
        
        # Check if repo contains Go code
        if not self._has_go_code(repo_path):
            logger.info(f"No Go code found in {repo_path}")
            return []
            
        try:
            # Run Gosec
            json_output = self._run_gosec(repo_path)
            if not json_output:
                logger.warning("Gosec scan produced no output")
                return []
                
            # Parse results
            findings = self._parse_results(json_output, repo_path)
            
            logger.info(f"Gosec scan completed with {len(findings)} findings")
            return findings
            
        except Exception as e:
            logger.error(f"Error during Gosec scan: {str(e)}")
            return []
    
    def _has_go_code(self, repo_path: str) -> bool:
        """Check if repository contains Go code"""
        try:
            result = subprocess.run(
                ["find", repo_path, "-name", "*.go", "-type", "f"],
                capture_output=True,
                text=True,
                check=False
            )
            return bool(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error checking for Go code: {str(e)}")
            return False
    
    def _run_gosec(self, repo_path: str) -> Optional[str]:
        """Run Gosec on Go code"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            output_file = tmp.name
            
        try:
            # Run Gosec with JSON output
            gosec_cmd = [
                self.gosec_path,
                "-fmt=json",
                "-out", output_file,
                "-exclude-dir=vendor",
                "-exclude-dir=.git",
                repo_path
            ]
            
            logger.info(f"Running Gosec command: {' '.join(gosec_cmd)}")
            process = subprocess.run(
                gosec_cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check for errors
            if process.returncode != 0 and process.returncode != 1:
                # Return code 1 is normal when issues are found
                logger.error(f"Gosec error: {process.stderr}")
                
            # Read output file
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                with open(output_file, "r") as f:
                    return f.read()
            else:
                logger.warning("Gosec output file is empty or missing")
                return None
                
        except Exception as e:
            logger.error(f"Error running Gosec: {str(e)}")
            return None
        finally:
            # Clean up temp file
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def _parse_results(self, json_output: str, repo_path: str) -> List[Finding]:
        """Parse Gosec JSON output into findings"""
        findings = []
        
        try:
            results = json.loads(json_output)
            issues = results.get("Issues", [])
            
            for issue in issues:
                severity = self._map_severity(issue.get("severity", ""))
                confidence = issue.get("confidence", "")
                
                file_path = issue.get("file", "")
                line = issue.get("line", "0")
                
                # Create finding
                finding = Finding(
                    id=f"GOSEC-{issue.get('rule_id', '')}-{hash(file_path + str(line))}",
                    tool="Gosec",
                    language="Go",
                    file=os.path.join(repo_path, file_path) if not file_path.startswith(repo_path) else file_path,
                    line=int(line),
                    cwe=self._extract_cwe(issue.get("cwe", "")),
                    severity=severity,
                    description=issue.get("details", ""),
                    evidence=issue.get("code", ""),
                    fix_suggestion=self._get_fix_suggestion(issue.get("rule_id", "")),
                    risk_score=self._calculate_risk_score(severity, confidence),
                    component=self._extract_component(file_path),
                    status="OPEN",
                    manual_review={},
                    reviewer_comments=[]
                )
                
                findings.append(finding)
                
        except Exception as e:
            logger.error(f"Error parsing Gosec results: {str(e)}")
            
        return findings
    
    def _map_severity(self, severity: str) -> SeverityLevel:
        """Map Gosec severity to severity level"""
        severity_map = {
            "HIGH": SeverityLevel.HIGH,
            "MEDIUM": SeverityLevel.MEDIUM,
            "LOW": SeverityLevel.LOW
        }
        return severity_map.get(severity.upper(), SeverityLevel.MEDIUM)
    
    def _extract_cwe(self, cwe_str: str) -> Optional[str]:
        """Extract CWE ID from Gosec CWE string"""
        if not cwe_str:
            return None
            
        # CWE strings can be in various formats
        if cwe_str.startswith("CWE-"):
            return cwe_str[4:]
        return cwe_str
    
    def _calculate_risk_score(self, severity: SeverityLevel, confidence: str) -> float:
        """Calculate risk score based on severity and confidence"""
        severity_score = {
            SeverityLevel.CRITICAL: 10.0,
            SeverityLevel.HIGH: 8.0,
            SeverityLevel.MEDIUM: 5.0,
            SeverityLevel.LOW: 2.0
        }.get(severity, 5.0)
        
        confidence_factor = {
            "HIGH": 1.0,
            "MEDIUM": 0.8,
            "LOW": 0.5
        }.get(confidence.upper(), 0.8)
        
        return severity_score * confidence_factor
    
    def _extract_component(self, file_path: str) -> str:
        """Extract component name from file path"""
        parts = file_path.split(os.path.sep)
        if len(parts) >= 2:
            return parts[-2]
        return os.path.basename(file_path)
    
    def _get_fix_suggestion(self, rule_id: str) -> str:
        """Get fix suggestion based on rule ID"""
        suggestions = {
            "G101": "Remove hardcoded credentials and use environment variables or a secure secret manager.",
            "G102": "Avoid using binding to all network interfaces (0.0.0.0) in production.",
            "G103": "Avoid using unsafe blocks as they bypass Go memory safety guarantees.",
            "G104": "Always check error returns to ensure proper error handling.",
            "G106": "Use SSH.InsecureIgnoreHostKey only in test code, never in production.",
            "G107": "Validate and sanitize URL parameters to prevent SSRF attacks.",
            "G108": "Avoid using unescaped variables in templates to prevent template injection.",
            "G109": "Use a cryptographically secure random number generator like crypto/rand.",
            "G110": "Avoid using strconv.Atoi to parse strings from untrusted sources.",
            "G201": "Use SQL prepared statements to prevent SQL injection.",
            "G202": "Use parameterized SQL queries to prevent SQL injection.",
            "G203": "Use proper HTML templating to prevent XSS.",
            "G204": "Validate and sanitize command arguments to prevent command injection.",
            "G301": "Use secure cryptographic algorithms and proper key sizes.",
            "G302": "Use secure TLS configurations with modern cipher suites.",
            "G303": "Use secure random number generation for cryptographic operations.",
            "G304": "Validate file paths to prevent path traversal vulnerabilities.",
            "G305": "Use filepath.Clean to sanitize file paths.",
            "G306": "Write files with appropriate permissions.",
            "G307": "Avoid using deferring Close() on HTTP response bodies.",
            "G401": "Use crypto/rand instead of math/rand for security-sensitive operations.",
            "G402": "Use TLS with proper certificate validation.",
            "G403": "Avoid using weak cryptographic primitives.",
            "G404": "Use secure random number generation for security-sensitive operations.",
            "G501": "Validate and sanitize inputs to prevent blacklisted imports.",
            "G502": "Avoid using deprecated or insecure cryptographic functions.",
            "G503": "Avoid using deprecated or insecure TLS configurations.",
            "G504": "Avoid using insecure cryptographic algorithms.",
            "G505": "Avoid using insecure cryptographic modes."
        }
        
        return suggestions.get(rule_id, "Review the code for security issues and apply appropriate fixes.")