import uuid
import re
from typing import List, Dict, Any, Set
from pathlib import Path
from ..models import Threat, ThreatCategory, SeverityLevel, Finding

STRIDE_RULES = [
    {
        "pattern": r"eval\(|exec\(",
        "threats": [ThreatCategory.TAMPERING, ThreatCategory.INFORMATION_DISCLOSURE],
        "cwe": "CWE-95",
        "severity": SeverityLevel.HIGH,
        "description": "Code injection via eval/exec",
        "attack_vector": "Attacker can execute arbitrary code",
        "mitre": ["T1059"],
        "mitigation": "Avoid using eval() or exec(). Use safer alternatives like ast.literal_eval() or JSON parsing."
    },
    {
        "pattern": r"os\.system\(|subprocess\.call\(|shell=True",
        "threats": [ThreatCategory.TAMPERING, ThreatCategory.ELEVATION_OF_PRIVILEGE],
        "cwe": "CWE-78",
        "severity": SeverityLevel.HIGH,
        "description": "Command injection vulnerability",
        "attack_vector": "Attacker can execute arbitrary system commands",
        "mitre": ["T1059.004"],
        "mitigation": "Use subprocess with argument lists instead of shell=True. Validate and sanitize all inputs."
    },
    {
        "pattern": r"\.execute\([^)]*%|\.execute\([^)]*\+|f\".*SELECT|f\".*INSERT|f\".*UPDATE",
        "threats": [ThreatCategory.TAMPERING, ThreatCategory.INFORMATION_DISCLOSURE],
        "cwe": "CWE-89",
        "severity": SeverityLevel.CRITICAL,
        "description": "SQL injection vulnerability",
        "attack_vector": "Attacker can manipulate database queries",
        "mitre": ["T1190"],
        "mitigation": "Use parameterized queries or ORM methods. Never concatenate user input into SQL."
    },
    {
        "pattern": r"password\s*=\s*['\"]|api_key\s*=\s*['\"]|secret\s*=\s*['\"]",
        "threats": [ThreatCategory.INFORMATION_DISCLOSURE],
        "cwe": "CWE-798",
        "severity": SeverityLevel.CRITICAL,
        "description": "Hardcoded credentials",
        "attack_vector": "Credentials exposed in source code",
        "mitre": ["T1552.001"],
        "mitigation": "Use environment variables or secure credential stores. Never hardcode secrets."
    },
    {
        "pattern": r"pickle\.loads|yaml\.load\(|deserialize",
        "threats": [ThreatCategory.TAMPERING, ThreatCategory.ELEVATION_OF_PRIVILEGE],
        "cwe": "CWE-502",
        "severity": SeverityLevel.HIGH,
        "description": "Insecure deserialization",
        "attack_vector": "Attacker can execute code through crafted serialized objects",
        "mitre": ["T1027"],
        "mitigation": "Use safe deserialization methods like yaml.safe_load(). Validate serialized data."
    },
    {
        "pattern": r"render_template_string|innerHTML|dangerouslySetInnerHTML",
        "threats": [ThreatCategory.TAMPERING, ThreatCategory.INFORMATION_DISCLOSURE],
        "cwe": "CWE-79",
        "severity": SeverityLevel.MEDIUM,
        "description": "Cross-site scripting (XSS) vulnerability",
        "attack_vector": "Attacker can inject malicious scripts",
        "mitre": ["T1059.007"],
        "mitigation": "Sanitize user input. Use framework-provided escaping mechanisms."
    },
    {
        "pattern": r"cors.*origin.*\*|Access-Control-Allow-Origin.*\*",
        "threats": [ThreatCategory.INFORMATION_DISCLOSURE, ThreatCategory.SPOOFING],
        "cwe": "CWE-942",
        "severity": SeverityLevel.MEDIUM,
        "description": "Overly permissive CORS policy",
        "attack_vector": "Any origin can access sensitive data",
        "mitre": ["T1557"],
        "mitigation": "Restrict CORS to specific trusted origins. Avoid wildcard (*) in production."
    },
    {
        "pattern": r"debug\s*=\s*True|DEBUG\s*=\s*True",
        "threats": [ThreatCategory.INFORMATION_DISCLOSURE],
        "cwe": "CWE-489",
        "severity": SeverityLevel.MEDIUM,
        "description": "Debug mode enabled",
        "attack_vector": "Sensitive information leaked in error messages",
        "mitre": ["T1592"],
        "mitigation": "Disable debug mode in production environments."
    },
    {
        "pattern": r"random\.random\(\)|Math\.random\(\)",
        "threats": [ThreatCategory.SPOOFING, ThreatCategory.ELEVATION_OF_PRIVILEGE],
        "cwe": "CWE-338",
        "severity": SeverityLevel.LOW,
        "description": "Weak random number generation",
        "attack_vector": "Predictable random values for security-sensitive operations",
        "mitre": ["T1552"],
        "mitigation": "Use cryptographically secure random generators (secrets module, crypto.randomBytes)."
    },
    {
        "pattern": r"admin|root|superuser",
        "threats": [ThreatCategory.ELEVATION_OF_PRIVILEGE],
        "cwe": "CWE-250",
        "severity": SeverityLevel.LOW,
        "description": "Potential privilege escalation path",
        "attack_vector": "Administrative functionality detected",
        "mitre": ["T1078"],
        "mitigation": "Implement proper access controls and role-based authorization."
    }
]

import logging

class StrideMapper:
    def __init__(self):
        self.logger = logging.getLogger("autothreatmap")
        self.rules = STRIDE_RULES

    def analyze_code(self, repo_path: str, findings: List[Finding]) -> List[Threat]:
        threats = []
        components = self._identify_components(repo_path)

        for component, files in components.items():
            component_threats = self._analyze_component(component, files, findings)
            threats.extend(component_threats)

        return threats

    def _identify_components(self, repo_path: str) -> Dict[str, List[str]]:
        components = {}
        repo = Path(repo_path)

        for file in repo.rglob("*"):
            if file.is_file() and file.suffix in [".py", ".js", ".java", ".ts", ".tsx"]:
                component_name = self._get_component_name(file, repo)
                if component_name not in components:
                    components[component_name] = []
                components[component_name].append(str(file))

        return components

    def _get_component_name(self, file: Path, repo: Path) -> str:
        rel_path = file.relative_to(repo)
        parts = rel_path.parts

        if len(parts) > 1:
            return parts[0]
        return "root"

    def _analyze_component(self, component: str, files: List[str], findings: List[Finding]) -> List[Threat]:
        threats = []
        detected_patterns: Set[str] = set()

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for rule in self.rules:
                    if re.search(rule["pattern"], content, re.IGNORECASE | re.MULTILINE):
                        pattern_key = f"{component}-{rule['cwe']}"

                        if pattern_key not in detected_patterns:
                            detected_patterns.add(pattern_key)

                            for threat_category in rule["threats"]:
                                threat = Threat(
                                    id=f"THREAT-{uuid.uuid4().hex[:8]}",
                                    category=threat_category,
                                    description=rule["description"],
                                    component=component,
                                    attack_vector=rule["attack_vector"],
                                    mitre_ids=rule["mitre"],
                                    cwe_ids=[rule["cwe"]],
                                    risk_level=rule["severity"],
                                    mitigation=rule["mitigation"]
                                )
                                threats.append(threat)
                                break
            except Exception as e:
                self.logger.error(f"Error analyzing file {file_path}: {e}")

        component_findings = [f for f in findings if component in f.file]
        for finding in component_findings:
            if finding.cwe and finding.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                threat = Threat(
                    id=f"THREAT-{uuid.uuid4().hex[:8]}",
                    category=ThreatCategory.TAMPERING,
                    description=f"Security finding: {finding.description}",
                    component=component,
                    attack_vector=f"Vulnerability detected by {finding.tool}",
                    mitre_ids=[],
                    cwe_ids=[finding.cwe] if finding.cwe else [],
                    risk_level=finding.severity,
                    mitigation=finding.fix_suggestion or "Review and remediate the security issue"
                )
                threats.append(threat)

        return threats

    def generate_attack_graph(self, threats: List[Threat]) -> Dict[str, Any]:
        import networkx as nx

        G = nx.DiGraph()

        components = set(t.component for t in threats)
        for comp in components:
            G.add_node(comp, node_type="component")

        for threat in threats:
            threat_node = f"{threat.id}"
            G.add_node(
                threat_node,
                node_type="threat",
                category=threat.category.value,
                severity=threat.risk_level.value,
                description=threat.description
            )
            G.add_edge(threat_node, threat.component, relationship="threatens")

        return {
            "nodes": [{"id": n, "data": G.nodes[n]} for n in G.nodes()],
            "edges": [{"source": u, "target": v, "data": G.edges[u, v]} for u, v in G.edges()],
            "summary": {
                "total_components": len(components),
                "total_threats": len(threats),
                "critical_threats": len([t for t in threats if t.risk_level == SeverityLevel.CRITICAL]),
                "high_threats": len([t for t in threats if t.risk_level == SeverityLevel.HIGH])
            }
        }
