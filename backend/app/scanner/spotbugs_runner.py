import logging
import subprocess
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

from ..models import Finding, SeverityLevel, ScanRequest

logger = logging.getLogger("autothreatmap.scanner.spotbugs")

class SpotBugsRunner:
    """
    SpotBugs scanner for Java code analysis
    """
    
    def __init__(self, spotbugs_path: Optional[str] = None):
        """
        Initialize the SpotBugs scanner
        
        Args:
            spotbugs_path: Path to SpotBugs installation (optional)
        """
        self.spotbugs_path = spotbugs_path or os.environ.get("SPOTBUGS_HOME", "/opt/spotbugs")
        
    async def scan(self, scan_request: ScanRequest) -> List[Finding]:
        """
        Run SpotBugs scan on Java code
        
        Args:
            scan_request: The scan request containing repo path
            
        Returns:
            List of security findings
        """
        repo_path = scan_request.repo_path
        logger.info(f"Starting SpotBugs scan on {repo_path}")
        
        # Check if repo contains Java code
        if not self._has_java_code(repo_path):
            logger.info(f"No Java code found in {repo_path}")
            return []
            
        try:
            # Step 1: Compile Java code if needed
            self._compile_java_code(repo_path)
            
            # Step 2: Run SpotBugs
            xml_output = self._run_spotbugs(repo_path)
            if not xml_output:
                logger.warning("SpotBugs scan produced no output")
                return []
                
            # Step 3: Parse results
            findings = self._parse_results(xml_output, repo_path)
            
            logger.info(f"SpotBugs scan completed with {len(findings)} findings")
            return findings
            
        except Exception as e:
            logger.error(f"Error during SpotBugs scan: {str(e)}")
            return []
    
    def _has_java_code(self, repo_path: str) -> bool:
        """Check if repository contains Java code"""
        try:
            result = subprocess.run(
                ["find", repo_path, "-name", "*.java", "-type", "f"],
                capture_output=True,
                text=True,
                check=False
            )
            return bool(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error checking for Java code: {str(e)}")
            return False
    
    def _compile_java_code(self, repo_path: str) -> None:
        """Compile Java code if needed"""
        # Check for Maven project
        if os.path.exists(os.path.join(repo_path, "pom.xml")):
            logger.info("Maven project detected, compiling with mvn")
            try:
                subprocess.run(
                    ["mvn", "compile", "-f", os.path.join(repo_path, "pom.xml")],
                    capture_output=True,
                    check=False
                )
                return
            except Exception as e:
                logger.error(f"Error compiling Maven project: {str(e)}")
                
        # Check for Gradle project
        if os.path.exists(os.path.join(repo_path, "build.gradle")):
            logger.info("Gradle project detected, compiling with gradle")
            try:
                subprocess.run(
                    ["gradle", "compileJava", "-p", repo_path],
                    capture_output=True,
                    check=False
                )
                return
            except Exception as e:
                logger.error(f"Error compiling Gradle project: {str(e)}")
                
        # Fallback to javac for simple projects
        logger.info("No build system detected, attempting direct compilation")
        try:
            java_files = subprocess.run(
                ["find", repo_path, "-name", "*.java"],
                capture_output=True,
                text=True,
                check=False
            ).stdout.strip().split("\n")
            
            if java_files:
                subprocess.run(
                    ["javac"] + java_files,
                    capture_output=True,
                    check=False
                )
        except Exception as e:
            logger.error(f"Error compiling Java files: {str(e)}")
    
    def _run_spotbugs(self, repo_path: str) -> Optional[str]:
        """Run SpotBugs on compiled Java code"""
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
            output_file = tmp.name
            
        try:
            # Determine class files location
            class_dirs = []
            
            # Check Maven target directory
            maven_target = os.path.join(repo_path, "target", "classes")
            if os.path.exists(maven_target):
                class_dirs.append(maven_target)
                
            # Check Gradle build directory
            gradle_build = os.path.join(repo_path, "build", "classes")
            if os.path.exists(gradle_build):
                for root, dirs, files in os.walk(gradle_build):
                    if files and any(f.endswith(".class") for f in files):
                        class_dirs.append(root)
                        
            # Fallback to searching for class files
            if not class_dirs:
                result = subprocess.run(
                    ["find", repo_path, "-name", "*.class"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.stdout.strip():
                    # Use parent directories of class files
                    class_paths = result.stdout.strip().split("\n")
                    class_dirs = list(set(os.path.dirname(p) for p in class_paths if p))
            
            if not class_dirs:
                logger.warning("No compiled Java classes found")
                return None
                
            # Run SpotBugs
            spotbugs_cmd = [
                os.path.join(self.spotbugs_path, "bin", "spotbugs"),
                "-textui",
                "-xml:withMessages",
                "-output", output_file
            ]
            
            # Add class directories
            for class_dir in class_dirs:
                spotbugs_cmd.extend(["-auxclasspath", class_dir])
                spotbugs_cmd.append(class_dir)
                
            logger.info(f"Running SpotBugs command: {' '.join(spotbugs_cmd)}")
            subprocess.run(
                spotbugs_cmd,
                capture_output=True,
                check=False
            )
            
            # Read output file
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                with open(output_file, "r") as f:
                    return f.read()
            else:
                logger.warning("SpotBugs output file is empty or missing")
                return None
                
        except Exception as e:
            logger.error(f"Error running SpotBugs: {str(e)}")
            return None
        finally:
            # Clean up temp file
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def _parse_results(self, xml_output: str, repo_path: str) -> List[Finding]:
        """Parse SpotBugs XML output into findings"""
        findings = []
        
        try:
            root = ET.fromstring(xml_output)
            
            # Get project name
            project_name = root.get("project", "Unknown")
            
            # Process each bug instance
            for bug_instance in root.findall(".//BugInstance"):
                bug_type = bug_instance.get("type", "")
                category = bug_instance.get("category", "")
                priority = int(bug_instance.get("priority", "3"))
                
                # Skip non-security bugs
                if category != "SECURITY" and not self._is_security_bug(bug_type):
                    continue
                
                # Get source line info
                source_line = bug_instance.find(".//SourceLine")
                if source_line is None:
                    continue
                    
                file_path = source_line.get("sourcepath", "")
                start_line = int(source_line.get("start", "0"))
                end_line = int(source_line.get("end", "0"))
                
                # Get class info
                class_element = bug_instance.find(".//Class")
                class_name = class_element.get("classname", "") if class_element is not None else ""
                
                # Get method info
                method_element = bug_instance.find(".//Method")
                method_name = method_element.get("name", "") if method_element is not None else ""
                
                # Get bug description
                bug_annotation = bug_instance.find(".//BugPattern")
                description = bug_annotation.get("shortDescription", "") if bug_annotation is not None else ""
                details = bug_annotation.text if bug_annotation is not None and bug_annotation.text else ""
                
                # Map priority to severity
                severity = self._map_priority_to_severity(priority)
                
                # Map to CWE if possible
                cwe_id = self._map_bug_to_cwe(bug_type)
                
                # Create finding
                finding = Finding(
                    id=f"SPOTBUGS-{bug_type}-{hash(file_path + str(start_line))}",
                    tool="SpotBugs",
                    language="Java",
                    file=os.path.join(repo_path, file_path) if not file_path.startswith(repo_path) else file_path,
                    line=start_line,
                    cwe=str(cwe_id) if cwe_id else None,
                    severity=severity,
                    description=f"{description}: {details}",
                    evidence=f"In class {class_name}, method {method_name}",
                    fix_suggestion=self._get_fix_suggestion(bug_type),
                    component=class_name,
                    status="OPEN",
                    manual_review={},
                    reviewer_comments=[]
                )
                
                findings.append(finding)
                
        except Exception as e:
            logger.error(f"Error parsing SpotBugs results: {str(e)}")
            
        return findings
    
    def _is_security_bug(self, bug_type: str) -> bool:
        """Check if bug type is security-related"""
        security_patterns = [
            "SECURITY", "INJECTION", "XSS", "SQL", "PATH", "COMMAND", "CRYPT", 
            "CIPHER", "HASH", "RANDOM", "PREDICTABLE", "TRUST", "PERMISSION"
        ]
        return any(pattern in bug_type.upper() for pattern in security_patterns)
    
    def _map_priority_to_severity(self, priority: int) -> SeverityLevel:
        """Map SpotBugs priority to severity level"""
        priority_map = {
            1: SeverityLevel.CRITICAL,  # High priority
            2: SeverityLevel.HIGH,
            3: SeverityLevel.MEDIUM,
            4: SeverityLevel.LOW,
            5: SeverityLevel.LOW
        }
        return priority_map.get(priority, SeverityLevel.MEDIUM)
    
    def _map_bug_to_cwe(self, bug_type: str) -> Optional[int]:
        """Map SpotBugs bug type to CWE ID"""
        # Common mappings based on SpotBugs bug patterns
        cwe_map = {
            "SQL_INJECTION": 89,  # SQL injection
            "SQL_INJECTION_JDBC": 89,
            "COMMAND_INJECTION": 78,  # OS command injection
            "XSS": 79,  # Cross-site scripting
            "PATH_TRAVERSAL": 22,  # Path traversal
            "WEAK_TRUST_MANAGER": 295,  # Certificate validation
            "WEAK_HOSTNAME_VERIFIER": 295,
            "WEAK_MESSAGE_DIGEST": 328,  # Weak hashing
            "CIPHER_INTEGRITY": 353,  # Missing MAC
            "ECB_MODE": 327,  # Weak encryption
            "STATIC_IV": 329,  # Predictable IV
            "HARD_CODE_PASSWORD": 798,  # Hardcoded credentials
            "HARD_CODE_KEY": 798,
            "PREDICTABLE_RANDOM": 338,  # Weak random
            "SERVLET_PARAMETER": 20,  # Improper input validation
            "SERVLET_CONTENT_TYPE": 79,
            "HTTP_RESPONSE_SPLITTING": 113,  # HTTP response splitting
            "INSECURE_COOKIE": 614,  # Insecure cookie
            "COOKIE_USAGE": 614,
            "JSP_JSTL_OUT": 79,  # XSS in JSP
            "SPRING_CSRF_PROTECTION_DISABLED": 352,  # CSRF
            "SPRING_CSRF_UNRESTRICTED_REQUEST_MAPPING": 352
        }
        
        for pattern, cwe in cwe_map.items():
            if pattern in bug_type:
                return cwe
                
        return None
    
    def _get_fix_suggestion(self, bug_type: str) -> str:
        """Get fix suggestion based on bug type"""
        suggestions = {
            "SQL_INJECTION": "Use parameterized queries or prepared statements instead of string concatenation.",
            "COMMAND_INJECTION": "Use ProcessBuilder with separate arguments instead of passing a full command string.",
            "XSS": "Use proper output encoding and context-specific escaping for user-controlled data.",
            "PATH_TRAVERSAL": "Validate and sanitize file paths, use canonical path resolution.",
            "WEAK_TRUST_MANAGER": "Implement proper certificate validation in your TrustManager.",
            "WEAK_HOSTNAME_VERIFIER": "Implement proper hostname verification in your HostnameVerifier.",
            "WEAK_MESSAGE_DIGEST": "Use stronger hashing algorithms like SHA-256 or SHA-3.",
            "CIPHER_INTEGRITY": "Use authenticated encryption modes like GCM instead of ECB/CBC.",
            "ECB_MODE": "Use a more secure mode like CBC with proper IV, or GCM.",
            "STATIC_IV": "Generate a new random IV for each encryption operation.",
            "HARD_CODE_PASSWORD": "Store secrets in a secure configuration or keystore, not in code.",
            "HARD_CODE_KEY": "Use a secure key management solution instead of hardcoding keys.",
            "PREDICTABLE_RANDOM": "Use SecureRandom instead of Random for security-sensitive operations.",
            "SERVLET_PARAMETER": "Validate and sanitize all user-provided input.",
            "HTTP_RESPONSE_SPLITTING": "Sanitize headers to prevent CRLF injection.",
            "INSECURE_COOKIE": "Set secure and httpOnly flags on sensitive cookies.",
            "JSP_JSTL_OUT": "Use <c:out> with escapeXml='true' to prevent XSS.",
            "SPRING_CSRF_PROTECTION_DISABLED": "Enable CSRF protection in your Spring Security configuration.",
            "SPRING_CSRF_UNRESTRICTED_REQUEST_MAPPING": "Add CSRF protection to your controller methods."
        }
        
        for pattern, suggestion in suggestions.items():
            if pattern in bug_type:
                return suggestion
                
        return "Review the code for security issues and apply appropriate fixes."