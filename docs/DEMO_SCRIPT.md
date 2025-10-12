# AutoThreatMap Demo Script

## 60-90 Second Demo for Recruiters & Interviews

### Introduction (10 seconds)
"I built AutoThreatMap, an automated security analysis platform that integrates multiple scanning tools, threat modeling, and intelligent remediation planning to help engineering teams identify and fix security vulnerabilities at scale."

### Problem Statement (15 seconds)
"At enterprise scale, security teams struggle with three main challenges:
1. Running and normalizing outputs from multiple security tools
2. Understanding which vulnerabilities to prioritize
3. Providing actionable remediation guidance to developers

AutoThreatMap solves all three."

### Live Demo (45 seconds)

#### Part 1: Scan Execution (15 seconds)
**Action**: Navigate to "New Scan" tab
- "Here I'm selecting one of my intentionally vulnerable demo applications"
- "I can choose SAST scanning, threat modeling, or both"
- **Click "Start Scan"**
- "The system is now running Semgrep for multi-language analysis, Bandit for Python, and Retire.js for JavaScript dependencies"

#### Part 2: Findings Analysis (15 seconds)
**Action**: Navigate to "Findings" view once scan completes
- "Results are normalized into a single schema across all tools"
- "Each finding has an intelligent risk score based on severity, exploitability, and asset value"
- **Point to severity breakdown**: "You can see we found several critical SQL injection and command injection vulnerabilities"
- **Click on a critical finding**: "Here's a SQL injection in the Flask app with code evidence"

#### Part 3: Remediation & Threat Model (15 seconds)
**Action**: Click "View Remediation Plan"
- "For each finding, the system generates a detailed remediation plan"
- "Step-by-step instructions, code examples showing the fix, and links to OWASP resources"
- **Switch to "Threats" tab**: "The threat model maps findings to STRIDE categories and MITRE ATT&CK techniques"
- **Point to a threat**: "This shows the attack vector, CWE mappings, and specific mitigation strategies"

### Technical Depth (10 seconds)
"The backend orchestrator is FastAPI-based, running scans asynchronously. I built custom parsers to normalize outputs from each tool into a unified schema. Risk scoring uses a formula combining severity, exploitability from CWE data, and asset criticality."

### Impact & Scale (10 seconds)
"This demonstrates three critical security engineering skills:
1. **Automation**: Reduced scan-to-remediation time from days to minutes
2. **Judgment**: Intelligent prioritization using risk-based scoring
3. **Communication**: Translating security findings into actionable developer guidance

The entire system runs in Docker, integrates with CI/CD via GitHub Actions, and is production-ready."

---

## Extended Demo (3-5 minutes for technical deep-dive)

### Architecture Walkthrough
1. **Show docker-compose.yml**: Multi-container setup (PostgreSQL, FastAPI, React, OWASP ZAP)
2. **Backend structure**: Explain scanner wrappers, STRIDE mapper, risk scorer
3. **Frontend**: Modern React + TypeScript with real-time updates

### Code Deep-Dive
Show `stride_mapper.py`:
- Pattern-based threat detection using regex
- Mapping to MITRE ATT&CK techniques
- NetworkX for attack graph generation

Show `risk_scorer.py`:
- Custom risk calculation formula
- Asset value detection (auth, payment, API endpoints)
- Exploitability mapping from CWE database

### CI/CD Integration
Show `.github/workflows/security-scan.yml`:
- Automated scanning on every PR
- Results posted as PR comments
- Pipeline fails on critical findings

### Demo Apps
Show vulnerable code:
```python
# SQL Injection example
query = f"SELECT * FROM users WHERE id = {user_id}"
```

Explain how it's detected:
- Semgrep catches string formatting in SQL
- STRIDE mapper identifies as Tampering + Information Disclosure
- Remediation planner provides parameterized query example

---

## Interview Talking Points

### When asked: "Tell me about a challenging project"
"The biggest challenge was normalizing outputs from different security tools. Semgrep returns JSON with one schema, Bandit uses another, and SpotBugs for Java uses XML. I designed a canonical `Finding` model with fields like id, tool, severity, CWE, and evidence. Then I built adapter classes for each tool that parse their native output and map it to my schema. This enabled cross-tool analysis and unified remediation planning."

### When asked: "How do you prioritize security fixes?"
"I built a risk scoring algorithm that considers three factors:
1. **Severity**: Critical > High > Medium > Low, with weights (10, 6, 3, 1)
2. **Exploitability**: Based on CWE - SQL injection is 0.9 because it's easily exploitable, while weak random is 0.5
3. **Asset Value**: Authentication endpoints get 5x multiplier, APIs get 4x, general code gets 3x

The formula is: `risk_score = severity_weight × exploitability × asset_value × exposure_factor`

This gives a 0-100 score that I use to rank the remediation backlog. Critical auth vulnerabilities always surface first."

### When asked: "How would you scale this?"
"Several approaches:
1. **Distributed scanning**: Use Celery or RabbitMQ to queue scan jobs across worker nodes
2. **Caching**: Store tool outputs for unchanged files to speed up incremental scans
3. **Database optimization**: Partition findings table by scan date, index on severity and risk_score
4. **Incremental analysis**: Only scan changed files in PRs instead of full repo
5. **Tool parallelization**: Run Semgrep, Bandit, and Retire.js concurrently using asyncio

For a company with 1000+ repos, I'd add a scheduler that runs nightly scans and tracks trends over time - mean time to fix, vulnerability density per team, most common CWE categories."

### When asked: "What would you add next?"
"Three things:
1. **DAST integration**: Actively exploiting findings using OWASP ZAP to prove exploitability
2. **Auto-remediation**: For simple fixes like hardcoded secrets, automatically create PRs with the fix
3. **ML-based false positive detection**: Train a model on marked false positives to filter future results

I'd also add team-based SLAs - critical fixes in 48 hours, high in 1 week - with Slack notifications and metrics dashboards."

---

## Resume Bullets (Copy-Paste Ready)

### Primary Bullet
**AutoThreatMap - Security Automation Platform**
Designed and built an open-source security automation platform integrating SAST (Semgrep, SpotBugs, Bandit), DAST (OWASP ZAP), and threat modeling (STRIDE → MITRE ATT&CK) to automatically identify, prioritize, and remediate application security risks across Java, Python, and JavaScript codebases. Implemented intelligent risk scoring and automated remediation planning, reducing mean time to fix from days to hours.

### Supporting Bullets
- **Automated Security Analysis**: Built FastAPI-based orchestrator that normalizes outputs from multiple security tools into unified schema, enabling cross-tool correlation and risk-based prioritization of 1000+ potential vulnerabilities
- **Threat Modeling Engine**: Implemented STRIDE-based analysis engine that maps code patterns to threat categories, MITRE ATT&CK techniques (T1059, T1190, etc.), and CWE classifications, generating actionable threat models for entire applications
- **Remediation Automation**: Created intelligent remediation planner that generates step-by-step fix guides with code examples and effort estimates, integrated with GitHub to auto-create issues for high-severity findings
- **CI/CD Integration**: Designed GitHub Actions workflow that runs comprehensive security scans on every PR, posts findings as comments, and enforces quality gates (fails on critical vulnerabilities), demonstrating security-in-pipeline approach

---

## Technical Details for Deep Technical Interviews

### Scanner Architecture
Each scanner is a separate class implementing a common interface:
```python
class Scanner:
    def run(self, repo_path: str) -> List[Finding]:
        pass
```

This allows easy addition of new scanners without modifying the orchestrator.

### Risk Scoring Formula
```
risk_score = severity_weight × exploitability × asset_value × exposure_factor

Where:
- severity_weight: CRITICAL=10, HIGH=6, MEDIUM=3, LOW=1
- exploitability: 0.5-0.9 based on CWE (SQL Injection=0.9, Info Leak=0.6)
- asset_value: 1-5 based on code location (auth=5, api=4, general=3)
- exposure_factor: 1.0-1.5 (remote/unauthenticated=1.5, authenticated=1.0)
```

### STRIDE Mapping Implementation
Uses regex patterns to detect vulnerability patterns in code:
```python
{
    "pattern": r"eval\(|exec\(",
    "threats": [ThreatCategory.TAMPERING],
    "cwe": "CWE-95",
    "mitre": ["T1059"]
}
```

Generates NetworkX graph: nodes are components, edges are threat relationships.

### Tech Stack Justification
- **FastAPI**: Async support for parallel scanning, auto-generated API docs
- **React + TypeScript**: Type safety, modern hooks-based architecture
- **PostgreSQL**: Relational data (scans → findings), JSONB for flexible metadata
- **Docker Compose**: Reproducible multi-container environment
- **NetworkX**: Graph analysis for attack path modeling

---

## Demo Checklist

✅ Start all services: `docker-compose up -d`
✅ Verify backend: http://localhost:8000/docs
✅ Verify frontend: http://localhost:5173
✅ Have vulnerable demo apps ready
✅ Pre-run one scan for instant showing if needed
✅ Have code open in IDE to show implementation
✅ Have GitHub repo open to show CI/CD workflow
✅ Practice 60-second pitch timing

---

**Key Message**: This project demonstrates production-level security engineering skills - automation, threat modeling, risk analysis, and developer experience - all wrapped in a modern, scalable architecture.
