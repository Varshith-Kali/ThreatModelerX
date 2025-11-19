# ThreatModelerX

> **Automated Security Analysis & Threat Modeling Platform**

ThreatModelerX is an open-source security automation platform that integrates SAST (Static Application Security Testing), threat modeling, and risk prioritization to automatically identify, map, and remediate application security risks across multiple programming languages.

![ThreatModelerX Dashboard](docs/screenshots/dashboard.png)

## Features

- **Multi-Tool SAST Integration**: Semgrep (multi-language), Bandit (Python), Retire.js (JavaScript)
- **Threat Modeling**: STRIDE-based analysis with MITRE ATT&CK and CWE mapping
- **Risk Scoring**: Intelligent prioritization based on severity, exploitability, and asset value
- **Automated Remediation Plans**: Step-by-step fix guides with code examples
- **Modern Web UI**: Real-time scan monitoring and interactive findings explorer
- **CI/CD Integration**: GitHub Actions workflow for automated scanning
- **Vulnerable Demo Apps**: Three intentionally vulnerable applications for testing

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   React UI      │────────▶│  FastAPI Backend │◀────────│  PostgreSQL DB  │
│  (Frontend)     │         │  (Orchestrator)  │         │  (Scan Results) │
└─────────────────┘         └────────┬─────────┘         └─────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
              │  Semgrep  │   │  Bandit   │   │ Retire.js │
              │  Scanner  │   │  Scanner  │   │  Scanner  │
              └───────────┘   └───────────┘   └───────────┘
                                     │
                              ┌──────▼──────┐
                              │   STRIDE    │
                              │Threat Model │
                              └─────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Running with Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/yourusername/auto-threatmap.git
cd auto-threatmap
```

2. Start all services:
```bash
docker-compose up -d
```

3. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Running Locally (Development)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
npm install
npm run dev
```

## Usage

### 1. Start a New Scan

Navigate to the "New Scan" tab and select a target application:
- Python Flask Demo (intentionally vulnerable)
- Node.js Express Demo (intentionally vulnerable)
- Or provide a custom repository path

Choose scan types:
- **SAST**: Static code analysis
- **Threat Modeling**: STRIDE-based threat identification

### 2. View Findings

Once the scan completes, findings are displayed with:
- Severity level (Critical, High, Medium, Low)
- Risk score (0-100)
- File location and line number
- CWE classification
- Evidence and code snippets

### 3. Get Remediation Plans

Click on any finding to view a detailed remediation plan including:
- Priority ranking
- Estimated effort
- Step-by-step fix instructions
- Code examples (before/after)
- Additional resources and documentation

### 4. Explore Threats

View the STRIDE threat model with:
- Threat categories (Spoofing, Tampering, Repudiation, etc.)
- Attack vectors
- MITRE ATT&CK technique mappings
- Mitigation strategies

## Demo Applications

### Python Flask Demo
Location: `demo-apps/python-flask/`

Vulnerabilities:
- SQL Injection (CWE-89)
- Command Injection (CWE-78)
- Insecure Deserialization (CWE-502)
- XSS (CWE-79)
- Code Injection (CWE-95)
- Hardcoded Credentials (CWE-798)

### Node.js Express Demo
Location: `demo-apps/node-express/`

Vulnerabilities:
- Command Injection (CWE-78)
- Code Injection (CWE-95)
- Hardcoded Credentials (CWE-798)
- Insecure CORS (CWE-942)
- Weak Random Number Generation (CWE-338)

## API Endpoints

### Scan Management
- `POST /api/scan` - Start a new security scan
- `GET /api/scan/{scan_id}` - Get scan status and results
- `GET /api/scans` - List all scans

### Findings
- `GET /api/findings` - Get all findings (filterable by severity, tool)
- `GET /api/findings?scan_id={id}` - Get findings for a specific scan

### Threats
- `GET /api/threats` - Get all threats
- `GET /api/threats?scan_id={id}` - Get threats for a specific scan

### Remediation
- `GET /api/remediation/{finding_id}` - Get remediation plan for a finding

### Statistics
- `GET /api/stats` - Get aggregated statistics

## CI/CD Integration

### GitHub Actions

Add the workflow file to `.github/workflows/security-scan.yml`:

```yaml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run AutoThreatMap Scan
        run: |
          docker-compose up -d backend
          # Wait for backend to be ready
          sleep 30
          # Trigger scan via API
          curl -X POST http://localhost:8000/api/scan \
            -H "Content-Type: application/json" \
            -d '{"repo_path": "./", "scan_types": ["sast", "threat_model"]}'
```

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Semgrep**: Multi-language static analysis
- **Bandit**: Python security linter
- **Retire.js**: JavaScript dependency scanner
- **NetworkX**: Graph analysis for threat modeling
- **PostgreSQL**: Scan results storage

### Frontend
- **React**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library
- **Vite**: Build tool and dev server

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **OWASP ZAP**: Dynamic application security testing (optional)
- **LocalStack**: AWS emulation for cloud security testing (optional)

## Project Structure

```
auto-threatmap/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Pydantic data models
│   │   ├── scanner/             # Scanner implementations
│   │   │   ├── semgrep_runner.py
│   │   │   ├── bandit_runner.py
│   │   │   └── retire_runner.py
│   │   ├── threatmodel/         # Threat modeling engine
│   │   │   └── stride_mapper.py
│   │   └── workers/             # Risk scoring & remediation
│   │       ├── risk_scorer.py
│   │       └── remediation_planner.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # React application
├── demo-apps/                   # Vulnerable demo applications
│   ├── python-flask/
│   └── node-express/
├── docs/                        # Documentation
├── docker-compose.yml
└── README.md
```

## Development

### Adding New Scanners

1. Create a new scanner class in `backend/app/scanner/`:
```python
from ..models import Finding, SeverityLevel

class MyScanner:
    def run(self, repo_path: str) -> List[Finding]:
        # Implementation
        pass
```

2. Register the scanner in `backend/app/main.py`:
```python
my_scanner = MyScanner()
findings = my_scanner.run(request.repo_path)
all_findings.extend(findings)
```

### Adding New STRIDE Rules

Edit `backend/app/threatmodel/stride_mapper.py` and add to `STRIDE_RULES`:
```python
{
    "pattern": r"your_regex_pattern",
    "threats": [ThreatCategory.TAMPERING],
    "cwe": "CWE-XXX",
    "severity": SeverityLevel.HIGH,
    "description": "Threat description",
    "attack_vector": "Attack vector description",
    "mitre": ["T1059"],
    "mitigation": "Mitigation steps"
}
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- OWASP for security best practices and tools
- MITRE for ATT&CK framework and CWE database
- All open-source security tool maintainers

## Contact & Support

- GitHub Issues: Report bugs or request features
- Documentation: See `/docs` folder for detailed guides
- Demo Video: [Link to demo video]

---

**Built for security engineers, by security engineers.**

Demonstrating automated security analysis, threat modeling, and remediation at scale.
