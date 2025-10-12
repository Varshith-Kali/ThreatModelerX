# Getting Started with AutoThreatMap

Welcome! This guide will get you up and running in 5 minutes.

## What is AutoThreatMap?

AutoThreatMap is a security automation platform that:
- Scans code for vulnerabilities using industry-standard tools
- Performs threat modeling using STRIDE framework
- Provides intelligent risk prioritization
- Generates step-by-step remediation plans

**Built for**: Security engineers, DevOps teams, and engineering managers who need to scale security across many projects.

---

## Quick Start (5 minutes)

### Option 1: Using the run script (Recommended)

```bash
./run.sh start
```

That's it! The script will:
1. Check Docker is running
2. Start all services
3. Wait for backend to be ready
4. Show you the URLs to access

### Option 2: Manual Docker Compose

```bash
docker-compose up -d
```

Wait ~60 seconds, then access:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

---

## Running Your First Scan

1. Open http://localhost:5173 in your browser
2. Click **"New Scan"** in the navigation bar
3. Select **"Python Flask (Vulnerable Demo)"** from the dropdown
4. Check both scan types:
   - ✅ Static Analysis (SAST)
   - ✅ Threat Modeling
5. Click **"Start Scan"**
6. Wait ~30 seconds for the scan to complete
7. Explore the results:
   - **Findings**: See all vulnerabilities detected
   - **Threats**: View STRIDE threat model
   - **Remediation**: Click any finding for fix guidance

---

## What You'll See

### Demo Results

**Python Flask App** will show:
- 12 vulnerabilities detected
- 3 Critical (SQL injection, command injection)
- 4 High (hardcoded secrets, insecure deserialization)
- 5 Medium (XSS, debug mode)

**Threat Model** will show:
- STRIDE category mappings
- MITRE ATT&CK techniques (T1059, T1190, etc.)
- Attack vectors and mitigations

**Remediation Plans** include:
- Step-by-step fix instructions
- Before/after code examples
- Links to OWASP resources
- Effort estimates

---

## Project Structure

```
auto-threatmap/
├── run.sh                    # Easy start script
├── docker-compose.yml        # Service orchestration
├── README.md                 # Main documentation
│
├── backend/                  # Python FastAPI
│   ├── app/
│   │   ├── scanner/         # Tool wrappers
│   │   ├── threatmodel/     # STRIDE analysis
│   │   └── workers/         # Risk scoring
│   └── requirements.txt
│
├── src/                      # React frontend
│   └── components/          # UI components
│
├── demo-apps/               # Vulnerable test apps
│   ├── python-flask/
│   └── node-express/
│
└── docs/                    # Documentation
    ├── DEMO_SCRIPT.md      # Interview guide
    ├── RESUME_BULLETS.md   # Career materials
    └── QUICK_START.md      # Detailed setup
```

---

## Common Commands

```bash
# Start everything
./run.sh start

# Stop everything
./run.sh stop

# View logs
./run.sh logs

# Check status
./run.sh status

# Rebuild after code changes
./run.sh rebuild

# Clean everything (removes data)
./run.sh clean
```

Or use docker-compose directly:
```bash
docker-compose up -d      # Start
docker-compose down       # Stop
docker-compose logs -f    # View logs
docker-compose ps         # Status
```

---

## Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Main web interface |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Health Check | http://localhost:8000/health | Service status |

---

## API Usage

### Start a scan programmatically

```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/demo-apps/python-flask",
    "scan_types": ["sast", "threat_model"]
  }'
```

Response:
```json
{
  "scan_id": "SCAN-a1b2c3d4",
  "status": "initiated"
}
```

### Check scan status

```bash
curl http://localhost:8000/api/scan/SCAN-a1b2c3d4
```

### Get findings

```bash
curl http://localhost:8000/api/findings?scan_id=SCAN-a1b2c3d4
```

### Get statistics

```bash
curl http://localhost:8000/api/stats
```

---

## Development Mode

### Backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (React)

```bash
npm install
npm run dev
```

---

## Troubleshooting

### Services won't start
```bash
docker-compose down
docker-compose up -d --build
```

### Port already in use
Edit `docker-compose.yml` and change the port:
```yaml
ports:
  - "8001:8000"  # Change first number
```

### Backend not responding
Check logs:
```bash
docker-compose logs backend
```

### Scan fails
Verify demo apps exist:
```bash
ls demo-apps/python-flask/app.py
ls demo-apps/node-express/app.js
```

---

## Next Steps

### 1. Explore the Demo Apps
Look at the intentionally vulnerable code:
- `demo-apps/python-flask/app.py`
- `demo-apps/node-express/app.js`

See how vulnerabilities are detected!

### 2. Try Different Scans
- Scan the Node.js Express app
- Try scanning your own code (copy to demo-apps/)
- Experiment with scan type combinations

### 3. Understand the Architecture
- Read `PROJECT_OVERVIEW.md` for technical details
- Check `backend/app/` for implementation
- Review `src/components/` for frontend code

### 4. Customize
- Add new STRIDE rules in `stride_mapper.py`
- Create new remediation templates
- Modify risk scoring weights

### 5. Integrate with CI/CD
- Copy `.github/workflows/security-scan.yml` to your repo
- Configure to run on PRs
- Automate security validation

---

## Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Main project documentation |
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Complete technical overview |
| [QUICK_START.md](docs/QUICK_START.md) | Detailed setup guide |
| [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | Interview demo guide |
| [RESUME_BULLETS.md](docs/RESUME_BULLETS.md) | Career materials |

---

## Key Features

✅ **Multi-Tool Integration**: Semgrep, Bandit, Retire.js
✅ **Threat Modeling**: STRIDE + MITRE ATT&CK
✅ **Risk Scoring**: Intelligent prioritization
✅ **Remediation Plans**: Step-by-step fix guides
✅ **Modern UI**: Real-time updates, responsive design
✅ **CI/CD Ready**: GitHub Actions workflow included
✅ **Production-Ready**: Docker, API docs, comprehensive logging

---

## Support

- **Issues**: Check `docker-compose logs` for errors
- **Questions**: Review documentation in `/docs`
- **Bugs**: Create GitHub issue with logs
- **Features**: Suggestions welcome!

---

## Demo Apps Security Warning

⚠️ **The demo applications contain intentional vulnerabilities!**

- Never deploy to production
- Never expose to the internet
- Use only in isolated development environments
- Do not use for security training without supervision

These apps are designed to be vulnerable for testing and demonstration purposes only.

---

## Success Checklist

After running `./run.sh start`, verify:

- [ ] Frontend loads at http://localhost:5173
- [ ] Backend responds at http://localhost:8000/health
- [ ] Can start a new scan
- [ ] Scan completes successfully
- [ ] Findings are displayed
- [ ] Threat model is shown
- [ ] Remediation plan opens

If all checked, you're ready to go!

---

## Quick Demo Script (30 seconds)

1. "This is AutoThreatMap - it automates security scanning and threat modeling"
2. Click "New Scan" → Select Python Flask → Start Scan
3. "It runs multiple security tools in parallel"
4. Wait for completion → Click "Findings"
5. "Here are 12 vulnerabilities detected, ranked by risk score"
6. Click a critical finding → "View Remediation Plan"
7. "Step-by-step fix guide with code examples"
8. Switch to "Threats" tab
9. "STRIDE threat model with MITRE ATT&CK mapping"
10. "All automated, production-ready, CI/CD integrated"

---

**Ready to scan? Run `./run.sh start` and open http://localhost:5173!**

Questions? Check the docs or create an issue.

Built for security engineers, by security engineers. 🔒
