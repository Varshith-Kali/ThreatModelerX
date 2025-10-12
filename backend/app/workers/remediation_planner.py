from ..models import Finding, RemediationPlan, SeverityLevel

class RemediationPlanner:
    REMEDIATION_TEMPLATES = {
        "CWE-89": {
            "steps": [
                "Identify all SQL query construction points in the code",
                "Replace string concatenation with parameterized queries",
                "Use ORM methods (e.g., SQLAlchemy, Django ORM) where possible",
                "Validate and sanitize user inputs",
                "Test with sqlmap or similar tools to verify fix"
            ],
            "code_snippet": """
# Bad - SQL injection vulnerable
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good - Parameterized query
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
""",
            "resources": [
                "https://owasp.org/www-community/attacks/SQL_Injection",
                "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
            ]
        },
        "CWE-78": {
            "steps": [
                "Replace os.system() or shell=True with subprocess with argument lists",
                "Validate and whitelist allowed commands",
                "Sanitize all user inputs passed to commands",
                "Use language-specific libraries instead of shell commands where possible",
                "Test with command injection payloads"
            ],
            "code_snippet": """
# Bad - Command injection vulnerable
os.system(f"ls {user_input}")

# Good - Safe subprocess usage
subprocess.run(["ls", user_input], check=True)
""",
            "resources": [
                "https://owasp.org/www-community/attacks/Command_Injection",
                "https://docs.python.org/3/library/subprocess.html#security-considerations"
            ]
        },
        "CWE-79": {
            "steps": [
                "Identify all user input rendering points",
                "Use framework-provided escaping (e.g., Jinja2 autoescape, React automatic escaping)",
                "Implement Content Security Policy (CSP) headers",
                "Validate and sanitize inputs on server side",
                "Use DOMPurify for client-side sanitization if needed"
            ],
            "code_snippet": """
# Bad - XSS vulnerable
html = f"<div>{user_input}</div>"

# Good - Use template engine with autoescape
template.render(user_input=user_input)
""",
            "resources": [
                "https://owasp.org/www-community/attacks/xss/",
                "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"
            ]
        },
        "CWE-798": {
            "steps": [
                "Remove hardcoded credentials from source code",
                "Store secrets in environment variables",
                "Use secret management tools (AWS Secrets Manager, HashiCorp Vault)",
                "Rotate compromised credentials immediately",
                "Add .env to .gitignore and scan history for leaked secrets"
            ],
            "code_snippet": """
# Bad - Hardcoded credentials
password = "admin123"

# Good - Use environment variables
import os
password = os.getenv("DB_PASSWORD")
""",
            "resources": [
                "https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password",
                "https://www.gitguardian.com/blog-secrets-in-code"
            ]
        },
        "CWE-502": {
            "steps": [
                "Replace pickle.loads() with JSON for data serialization",
                "If pickle is required, verify data source and integrity",
                "Use yaml.safe_load() instead of yaml.load()",
                "Implement input validation before deserialization",
                "Consider using safer formats like JSON or Protocol Buffers"
            ],
            "code_snippet": """
# Bad - Insecure deserialization
obj = pickle.loads(user_data)

# Good - Use JSON
import json
obj = json.loads(user_data)
""",
            "resources": [
                "https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data",
                "https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html"
            ]
        }
    }

    def create_plan(self, finding: Finding) -> RemediationPlan:
        priority = self._calculate_priority(finding)
        effort = self._estimate_effort(finding)

        template = self.REMEDIATION_TEMPLATES.get(finding.cwe, {
            "steps": ["Review the security issue", "Apply appropriate fixes", "Test the changes"],
            "code_snippet": None,
            "resources": ["https://cwe.mitre.org/"]
        })

        plan = RemediationPlan(
            finding_id=finding.id,
            priority=priority,
            estimated_effort=effort,
            steps=template["steps"],
            code_snippet=template.get("code_snippet"),
            resources=template.get("resources", [])
        )

        return plan

    def _calculate_priority(self, finding: Finding) -> int:
        if finding.severity == SeverityLevel.CRITICAL:
            return 1
        elif finding.severity == SeverityLevel.HIGH:
            return 2 if finding.risk_score and finding.risk_score > 50 else 3
        elif finding.severity == SeverityLevel.MEDIUM:
            return 4
        else:
            return 5

    def _estimate_effort(self, finding: Finding) -> str:
        effort_map = {
            "CWE-798": "1-2 hours",
            "CWE-489": "30 minutes",
            "CWE-89": "2-4 hours",
            "CWE-78": "2-4 hours",
            "CWE-79": "1-3 hours",
            "CWE-502": "2-6 hours",
            "CWE-942": "1 hour",
            "CWE-338": "1-2 hours"
        }

        return effort_map.get(finding.cwe, "2-4 hours")
